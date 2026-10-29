from dash import html, dcc
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from get_data import get_data

def create_figure_linechart(dataset_url, log10=True, selected_sites=None, reference_url=None):
    result = get_data(dataset_url, reference_url, log10=log10)
    df_elt = result["elements"]
    df_data = result["data"]
    df_data['label'] = '<b>' + df_data['context_name'] + '</b>' + " - " + df_data['sample_name']

    # Assign 1 color per unique context_name
    unique_sites = df_data["context_name"].unique()
    colors = px.colors.qualitative.Alphabet  # or any palette
    site_color_map = {site: colors[i % len(colors)] for i, site in enumerate(unique_sites)}

    # HTML-safe reference string
    refbib = html.A(df_data.at[0, 'reference'], href=df_data.at[0, 'url'], target='_blank')

    fig = go.Figure()

    for idx, row in df_elt.iterrows():
        site = df_data.loc[idx, 'context_name']
        if selected_sites and site not in selected_sites:
            continue

        label = df_data.loc[idx, 'label']
        color = site_color_map[site]   # ← always the same per site
        customdata = [[label] for _ in df_elt.columns]

        fig.add_trace(go.Scatter(
            x=df_elt.columns,
            y=row.values,
            mode='lines+markers',
            line=dict(color=color),   # ← uniform color assignment
            marker=dict(color=color),
            customdata=customdata,
            hovertemplate='%{customdata[0]}<br><b>elt</b>: %{x} | <b>val</b>: %{y:.3f}<extra></extra>',
            name=label
        ))

    fig.update_layout(
        xaxis_title="Element",
        yaxis_title="Log10 Value" if log10 else "Original Value",
        height=600,
        margin=dict(t=20, 
                    b=10, 
                    l=10, 
                    r=10)
    )
    
    ref_html = html.Div([
        # html.H4("Sources & References"),
        html.Ul([
            html.Li([
                html.Span("Reference: "),
                refbib, html.Span("  "),
                html.Img(
                        src="/dash/assets/lod-licences-cc-by.png",
                        style={
                            "height": "25px",
                            "verticalAlign": "middle",
                            "marginRight": "5px"
                            }
                         )
            ]),
            html.Li([
                html.Span("Data: "), 
                html.A("API", href=dataset_url, target="_blank"), 
                html.Span(" | "), 
                html.A("CSV", id='download-csv-btn', n_clicks=0, href="#"), dcc.Download(id='download-csv')
            ]),
        ])
    ], style={'marginTop': '0px'})

    return fig, ref_html


def _empty_ternary_figure(message, dataset_url, refbib):
    # TODO: generic function for empty figure with reference info
    # TODO: add a link with the message, to the API
    # fig = go.Figure()
    # fig.update_layout(
    #     title=message,
    #     height=150,
    #     margin=dict(t=50, b=50, l=50, r=50),
    #     ternary=dict(sum=100)
    # )
    fig = go.Figure()
    fig.add_annotation(
        text=message, # 
        x=0.5,
        y=0.5,
        xref="paper",
        yref="paper",
        showarrow=False,
        font=dict(size=24),
        align="center"
    )

    fig.update_layout(
        height=400,
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(t=20, b=20, l=20, r=20),
    )

    ref_html = html.Div([
        html.Ul([
            html.Li([html.Span("Reference: "), refbib]),
            html.Li([html.Span("Data: "),
                     html.A("API", href=dataset_url, target="_blank")])
        ])
    ])

    return fig, ref_html


def create_figure_ternary(dataset_url, log10=False, selected_sites=None, tern_axes="FeO_SiO2_Al2O3", reference_url=None):
    """
    Create a ternary plot from a dataset, after converting elements -> oxides.

    tern_axes:
      - "FeO_SiO2_Al2O3" (default)
      - "FeO_MnO_CaO"
      - "FeO_K2O_P2O5"
    """
    import pandas as pd
    import plotly.express as px
    import plotly.graph_objects as go
    from dash import html

    result = get_data(dataset_url, reference_url, log10=log10)
    df_data = result["data"].copy()

    if selected_sites:
        df_data = df_data[df_data["context_name"].isin(selected_sites)].copy()
        
    df_data["label"] = "<b>" + df_data["context_name"].astype(str) + "</b> - " + df_data["sample_name"].astype(str)
    refbib = html.A(df_data.at[df_data.index[0], "reference"], href=df_data.at[df_data.index[0], "url"], target="_blank")

    # Element -> oxide conversion factors
    conversion_factors = {
        "Na": ("Na2O", 1.348),
        "Mg": ("MgO", 1.658),
        "Al": ("Al2O3", 1.889),
        "Si": ("SiO2", 2.139),
        "P":  ("P2O5", 2.291),
        "K":  ("K2O", 1.204),
        "Ca": ("CaO", 1.399),
        "Mn": ("MnO", 1.291),
        "Fe": ("FeO", 1.287),
    }

    oxide_data = {}
    for elem, (oxide_name, factor) in conversion_factors.items():
        if elem in df_data.columns:
            df_data[elem] = pd.to_numeric(df_data[elem], errors="coerce")
            oxide_data[oxide_name] = df_data[elem] * factor

    oxides_df = pd.DataFrame(oxide_data, index=df_data.index)
    merged_df = pd.concat([df_data, oxides_df], axis=1)

    # Map the radio selection to the 3 oxides
    axes_map = {
        "FeO_SiO2_Al2O3": ("FeO", "SiO2", "Al2O3"),
        "FeO_MnO_CaO": ("FeO", "MnO", "CaO"),
        "FeO_K2O_P2O5": ("FeO", "K2O", "P2O5"),
    }
    a_ox, b_ox, c_ox = axes_map.get(tern_axes, axes_map["FeO_SiO2_Al2O3"])

    # required = [a_ox, b_ox, c_ox]
    # missing = [c for c in required if c not in merged_df.columns]
    # if missing:
    #     fig = go.Figure()
    #     fig.update_layout(
    #         title=f"Missing required columns for ternary: {', '.join(missing)}",
    #         height=600,
    #         margin=dict(t=50, 
    #                     b=50, 
    #                     l=50, 
    #                     r=50),
    #     )
    #     ref_html = html.Div([
    #         html.Ul([
    #             html.Li([html.Span("Reference: "), refbib]),
    #             html.Li([html.Span("Data: "), html.A("API", href=dataset_url, target="_blank")]),
    #         ])
    #     ])
    #     return fig, ref_html
    required = [a_ox, b_ox, c_ox]
    # Check missing columns
    missing = [c for c in required if c not in merged_df.columns]
    if missing:
        return _empty_ternary_figure(
            f"Missing required columns for ternary: {', '.join(missing)}",
            dataset_url,
            refbib
        )

    # Check columns that exist but are fully NaN or zero
    invalid = []
    for col in required:
        if merged_df[col].dropna().empty or merged_df[col].sum(skipna=True) == 0:
            invalid.append(col)

    if invalid:
        return _empty_ternary_figure(
            f"No usable data for: {', '.join(invalid)}",
            dataset_url,
            refbib
        )

    # Normalize the chosen oxides to 100
    total = merged_df[required].sum(axis=1)
    merged_df = merged_df[total > 0].copy()

    a_pct = f"{a_ox}_pct"
    b_pct = f"{b_ox}_pct"
    c_pct = f"{c_ox}_pct"

    merged_df[a_pct] = merged_df[a_ox] * 100.0 / merged_df[required].sum(axis=1)
    merged_df[b_pct] = merged_df[b_ox] * 100.0 / merged_df[required].sum(axis=1)
    merged_df[c_pct] = merged_df[c_ox] * 100.0 / merged_df[required].sum(axis=1)

    hover_data = {
        a_pct: ":.2f",
        b_pct: ":.2f",
        c_pct: ":.2f",
        "typology": True,
    }

    fig = px.scatter_ternary(
        merged_df,
        a=a_pct,
        b=b_pct,
        c=c_pct,
        color="context_name",
        hover_name="label",
        hover_data=hover_data,
    )

    fig.update_layout(
        height=600,
        margin=dict(t=50, 
                    b=50, 
                    l=50, 
                    r=50),
        ternary=dict(
            sum=100,
            aaxis_title=f"{a_ox} (%)",
            baxis_title=f"{b_ox} (%)",
            caxis_title=f"{c_ox} (%)",
        ),
        legend_title_text="context_name",
    )

    ref_html = html.Div([
        html.Ul([
            html.Li([
                html.Span("Reference: "),
                refbib, html.Span("  "),
                html.Img(
                    src="/dash/assets/lod-licences-cc-by.png",
                    style={"height": "25px", "verticalAlign": "middle", "marginRight": "5px"}
                )
            ]),
            html.Li([
                html.Span("Data: "),
                html.A("API", href=dataset_url, target="_blank"),
                html.Span(" | "),
                html.A("CSV", id="tern-download-csv-btn", n_clicks=0, href="#"),
                dcc.Download(id="tern-download-csv"),
            ]),
        ])
    ], style={"marginTop": "0px"})

    return fig, ref_html


