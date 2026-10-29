"""Plotly figures and shared archaeometric transformations."""
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import html, dcc
from get_data import get_data

OXIDE_FACTORS = {
    "Na": ("Na2O", 1.348), "Mg": ("MgO", 1.658),
    "Al": ("Al2O3", 1.889), "Si": ("SiO2", 2.139),
    "P": ("P2O5", 2.291), "K": ("K2O", 1.204),
    "Ca": ("CaO", 1.399), "Mn": ("MnO", 1.291),
    "Fe": ("FeO", 1.287),
}
TERNARY_AXES = {
    "FeO_SiO2_Al2O3": ("FeO", "SiO2", "Al2O3"),
    "FeO_MnO_CaO": ("FeO", "MnO", "CaO"),
    "FeO_K2O_P2O5": ("FeO", "K2O", "P2O5"),
}


def add_oxides(df):
    """Convert elemental concentrations to oxides; retain source columns."""
    out = df.copy()
    for element, (oxide, factor) in OXIDE_FACTORS.items():
        if element in out.columns:
            out[oxide] = pd.to_numeric(out[element], errors="coerce") * factor
    return out


def reference_info(df, dataset_url, prefix):
    """Shared reference and CSV download controls for each chart."""
    entries = []
    if not df.empty and {"reference", "url"}.issubset(df.columns):
        row = df.iloc[0]
        if pd.notna(row["reference"]):
            entries.append(html.Li([
                html.Span("Reference: "),
                html.A(str(row["reference"]), href=str(row["url"]) if pd.notna(row["url"]) else None,
                       target="_blank"), html.Span("  "),
                html.Img(src="/dash/assets/lod-licences-cc-by.png",
                         style={"height": "25px", "verticalAlign": "middle"}),
            ]))
    entries.append(html.Li([
        html.Span("Data: "), html.A("API", href=dataset_url, target="_blank"),
        html.Span(" | "), html.A("CSV", id=f"{prefix}-download-csv-btn", n_clicks=0, href="#"),
        dcc.Download(id=f"{prefix}-download-csv"),
    ]))
    return html.Div(html.Ul(entries), style={"marginTop": "0px"})


def empty_figure(message):
    fig = go.Figure()
    fig.add_annotation(text=message, x=0.5, y=0.5, xref="paper", yref="paper",
                       showarrow=False, font={"size": 18})
    fig.update_layout(height=500, xaxis={"visible": False}, yaxis={"visible": False})
    return fig


def filter_contexts(df, selected_sites):
    # None means the selection has not yet been initialized; [] means unselect all.
    if selected_sites is None:
        return df.copy()
    return df.loc[df["context_name"].isin(selected_sites)].copy()


def create_figure_linechart(dataset_url, log10=True, selected_sites=None, reference_url=None):
    result = get_data(dataset_url, reference_url, log10=log10)
    original = result["data"]
    ref = reference_info(original, dataset_url, "line")
    data = filter_contexts(original, selected_sites)
    if data.empty:
        return empty_figure("No samples in the selected contexts"), ref
    elements = result["elements"].loc[data.index]
    colors = px.colors.qualitative.Alphabet
    all_contexts = original["context_name"].dropna().unique()
    palette = {site: colors[i % len(colors)] for i, site in enumerate(all_contexts)}
    fig = go.Figure()
    for idx, row in elements.iterrows():
        sample = data.loc[idx]
        site = sample["context_name"]
        label = f"<b>{site}</b> - {sample.get('sample_name', '')}"
        fig.add_trace(go.Scatter(
            x=elements.columns, y=row.values, mode="lines+markers",
            line={"color": palette.get(site, colors[0])},
            marker={"color": palette.get(site, colors[0])},
            customdata=[[label]] * len(elements.columns),
            hovertemplate="%{customdata[0]}<br><b>elt</b>: %{x} | <b>val</b>: %{y:.3f}<extra></extra>",
            name=label,
        ))
    fig.update_layout(xaxis_title="Element", yaxis_title="Log10 Value" if log10 else "Original Value",
                      height=600, margin={"t": 20, "b": 10, "l": 10, "r": 10})
    return fig, ref


def create_figure_scatter(dataset_url, y_oxide="Al2O3", selected_sites=None, reference_url=None):
    """FeO versus Al2O3 or SiO2; OLS fitted to all visible samples."""
    original = get_data(dataset_url, reference_url, log10=False)["data"]
    ref = reference_info(original, dataset_url, "scatter")
    if y_oxide not in ("Al2O3", "SiO2"):
        return empty_figure("Unknown Y-axis oxide"), ref
    data = add_oxides(filter_contexts(original, selected_sites))
    required = ["FeO", y_oxide]
    missing = [col for col in required if col not in data.columns]
    if missing:
        return empty_figure("Missing required oxides: " + ", ".join(missing)), ref
    data[required] = data[required].apply(pd.to_numeric, errors="coerce")
    data = data.replace([np.inf, -np.inf], np.nan).dropna(subset=required)
    if data.empty:
        return empty_figure("No valid samples for this oxide pair"), ref
    data["label"] = data.get("sample_name", pd.Series("", index=data.index)).astype(str)
    fig = px.scatter(data, x="FeO", y=y_oxide, color="context_name", hover_name="label",
                     hover_data={"FeO": ":.3f", y_oxide: ":.3f"})
    x = data["FeO"].to_numpy(dtype=float)
    y = data[y_oxide].to_numpy(dtype=float)
    if len(x) >= 2 and np.unique(x).size >= 2:
        slope, intercept = np.polyfit(x, y, 1)
        predicted = slope * x + intercept
        ss_total = np.sum((y - y.mean()) ** 2)
        r_squared = 1 - np.sum((y - predicted) ** 2) / ss_total if ss_total > 0 else float("nan")
        x_line = np.array([x.min(), x.max()])
        label = f"OLS regression (n={len(x)}, R²={r_squared:.3f})" if np.isfinite(r_squared) else f"OLS regression (n={len(x)})"
        fig.add_trace(go.Scatter(x=x_line, y=slope * x_line + intercept,
                                 mode="lines", name=label,
                                 line={"color": "black", "width": 2, "dash": "dash"},
                                 hovertemplate=f"y = {slope:.4g}x {intercept:+.4g}<extra></extra>"))
    else:
        fig.add_annotation(text="Regression requires two distinct FeO values", x=0.5, y=1.04,
                           xref="paper", yref="paper", showarrow=False)
    fig.update_layout(height=600, xaxis_title="FeO (converted oxide values)",
                      yaxis_title=f"{y_oxide} (converted oxide values)",
                      legend_title_text="Context", margin={"t": 45, "b": 35, "l": 30, "r": 20})
    return fig, ref


def create_figure_ternary(dataset_url, log10=False, selected_sites=None,
                          tern_axes="FeO_SiO2_Al2O3", reference_url=None):
    original = get_data(dataset_url, reference_url, log10=False)["data"]
    ref = reference_info(original, dataset_url, "ternary")
    data = add_oxides(filter_contexts(original, selected_sites))
    required = TERNARY_AXES.get(tern_axes, TERNARY_AXES["FeO_SiO2_Al2O3"])
    missing = [col for col in required if col not in data.columns]
    if missing:
        return empty_figure("Missing required oxides: " + ", ".join(missing)), ref
    data[list(required)] = data[list(required)].apply(pd.to_numeric, errors="coerce")
    data = data.replace([np.inf, -np.inf], np.nan).dropna(subset=list(required))
    data = data.loc[(data[list(required)] >= 0).all(axis=1)].copy()
    total = data[list(required)].sum(axis=1)
    data = data.loc[total > 0].copy()
    if data.empty:
        return empty_figure("No usable samples for this ternary plot"), ref
    pct = []
    for col in required:
        name = f"{col}_pct"
        data[name] = data[col] * 100 / data[list(required)].sum(axis=1)
        pct.append(name)
    data["label"] = data["context_name"].astype(str) + " - " + data["sample_name"].astype(str)
    hover_data = {name: ":.2f" for name in pct}
    if "typology" in data.columns:
        hover_data["typology"] = True
    fig = px.scatter_ternary(data, a=pct[0], b=pct[1], c=pct[2],
                             color="context_name", hover_name="label", hover_data=hover_data)
    fig.update_layout(height=600, margin={"t": 50, "b": 50, "l": 50, "r": 50},
                      ternary={"sum": 100, "aaxis_title": f"{required[0]} (%)",
                               "baxis_title": f"{required[1]} (%)", "caxis_title": f"{required[2]} (%)"},
                      legend_title_text="Context")
    return fig, ref
