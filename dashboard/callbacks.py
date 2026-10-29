"""Dash callbacks for maps and the three shared chart views."""
import dash
from dash import dcc, html, Input, Output, State
from get_data import get_data
from charts import create_figure_linechart, create_figure_scatter, create_figure_ternary
from pages import render_page


def register_callbacks(app, df, dataset_slugs, dataset_map, dataset_map_nums, coloramp_all_dataset_map):
    reference_url = df["url_reference"]

    @app.callback(Output("page-content", "children"), Input("url", "pathname"), State("url", "search"))
    def display_page(pathname, search):
        return render_page(pathname, search, df, dataset_slugs, dataset_map,
                           dataset_map_nums, coloramp_all_dataset_map)

    @app.callback(Output("map-row-count", "children"), Input("map-current-dataset-url", "data"))
    def update_map_row_count(dataset_url):
        if not dataset_url:
            return ""
        data = get_data(dataset_url, reference_url, log10=False)["data"]
        return html.Div([html.Strong("Samples: "), f"{len(data):,}", html.Br(),
                         html.Strong("Sites: "), f"{data['context_name'].nunique()}"])

    @app.callback(Output("map-download-csv", "data"), Input("map-download-csv-btn", "n_clicks"),
                  State("map-current-dataset-url", "data"), State("map-current-slug", "data"),
                  prevent_initial_call=True)
    def download_map_csv(n_clicks, dataset_url, slug):
        data = get_data(dataset_url, reference_url, log10=False)["data"]
        return dcc.send_data_frame(data.to_csv, f"chips_{slug}_data.csv", index=False)

    @app.callback(Output("line-graph", "figure"), Output("line-reference-info", "children"),
                  Input("line-scale-selector", "value"), Input("line-current-dataset-url", "data"),
                  Input("line-site-filter", "value"))
    def update_line(scale_mode, dataset_url, selected_sites):
        return create_figure_linechart(dataset_url, log10=(scale_mode == "log"),
                                       selected_sites=selected_sites, reference_url=reference_url)

    @app.callback(Output("scatter-graph", "figure"), Output("scatter-reference-info", "children"),
                  Input("scatter-current-dataset-url", "data"), Input("scatter-site-filter", "value"),
                  Input("scatter-y-selector", "value"))
    def update_scatter(dataset_url, selected_sites, y_oxide):
        return create_figure_scatter(dataset_url, y_oxide=y_oxide,
                                     selected_sites=selected_sites, reference_url=reference_url)

    @app.callback(Output("ternary-graph", "figure"), Output("ternary-reference-info", "children"),
                  Input("ternary-current-dataset-url", "data"), Input("ternary-site-filter", "value"),
                  Input("ternary-axes-selector", "value"))
    def update_ternary(dataset_url, selected_sites, tern_axes):
        return create_figure_ternary(dataset_url, selected_sites=selected_sites,
                                     tern_axes=tern_axes, reference_url=reference_url)

    # Register three structurally identical context selectors.
    def register_context_selector(prefix):
        @app.callback(Output(f"{prefix}-site-filter", "options"),
                      Output(f"{prefix}-site-filter", "value"),
                      Input(f"{prefix}-current-dataset-url", "data"),
                      Input(f"{prefix}-select-all-sites", "n_clicks"),
                      Input(f"{prefix}-unselect-all-sites", "n_clicks"))
        def update_contexts(dataset_url, select_clicks, unselect_clicks):
            if not dataset_url:
                return [], []
            data = get_data(dataset_url, reference_url, log10=False)["data"]
            contexts = sorted(data["context_name"].dropna().unique().tolist())
            options = [{"label": name, "value": name} for name in contexts]
            triggered = dash.ctx.triggered_id
            if triggered == f"{prefix}-unselect-all-sites":
                return options, []
            return options, contexts
        return update_contexts

    for prefix in ("line", "scatter", "ternary"):
        register_context_selector(prefix)

    def register_csv_download(prefix):
        @app.callback(Output(f"{prefix}-download-csv", "data"),
                      Input(f"{prefix}-download-csv-btn", "n_clicks"),
                      State(f"{prefix}-current-dataset-url", "data"),
                      State(f"{prefix}-current-slug", "data"),
                      State(f"{prefix}-site-filter", "value"),
                      prevent_initial_call=True)
        def download_csv(n_clicks, dataset_url, slug, selected_sites):
            data = get_data(dataset_url, reference_url, log10=False)["data"]
            if selected_sites is not None:
                data = data.loc[data["context_name"].isin(selected_sites)]
            return dcc.send_data_frame(data.to_csv, f"chips_{slug}_data.csv", index=False)
        return download_csv

    for prefix in ("line", "scatter", "ternary"):
        register_csv_download(prefix)
