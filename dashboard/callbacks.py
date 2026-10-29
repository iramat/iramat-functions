import dash
from dash import dcc, html, Input, Output, State
from get_data import get_data
from charts import create_figure_linechart, create_figure_ternary
from pages import render_page

def register_callbacks(app, df, dataset_slugs, dataset_map, dataset_map_nums, coloramp_all_dataset_map):
    reference_url = df["url_reference"]

    @app.callback(
        Output("page-content", "children"),
        Input("url", "pathname"),
        State("url", "search")
    )
    def display_page(pathname, search):
        return render_page(pathname, search, df, dataset_slugs, dataset_map, dataset_map_nums, coloramp_all_dataset_map)

    @app.callback(
        Output("map-row-count", "children"),
        Input("map-current-dataset-url", "data")
    )
    def update_map_row_count(dataset_url):
        if not dataset_url:
            return ""

        result = get_data(dataset_url, reference_url, log10=False)
        df_data = result["data"]

        return html.Div([
            html.Strong("Samples: "),
            f"{len(df_data):,}",
            html.Br(),
            html.Strong("Sites: "),
            f"{df_data['context_name'].nunique()}"
        ])


    @app.callback(
        Output("map-download-csv", "data"),
        Input("map-download-csv-btn", "n_clicks"),
        State("map-current-dataset-url", "data"),
        State("map-current-slug", "data"),
        prevent_initial_call=True
    )
    def download_map_csv(n_clicks, dataset_url, slug):
        result = get_data(dataset_url, reference_url, log10=False)
        df_data = result["data"]
        return dcc.send_data_frame(
            df_data.to_csv,
            f"chips_{slug}_data.csv",
            index=False
        )


    @app.callback(
        Output('dataset-graph', 'figure'),
        Output('reference-info', 'children'),
        Input('scale-selector', 'value'),
        Input('current-dataset-url', 'data'),
        Input('site-filter', 'value')
    )
    def update_graph(scale_mode, dataset_url, selected_sites):
        """Update the linechart"""
        log10 = scale_mode == 'log'
        fig, ref_html = create_figure_linechart(dataset_url, log10=log10, selected_sites=selected_sites, reference_url=reference_url)
        return fig, ref_html


    @app.callback(
        Output("ternary-graph", "figure"),
        Output("tern-reference-info", "children"),
        Input("tern-current-dataset-url", "data"),
        Input("tern-site-filter", "value"),
        Input("tern-axes-selector", "value"),   # NEW
    )
    def update_ternary_graph(dataset_url, selected_sites, tern_axes):
        fig, ref_html = create_figure_ternary(
            dataset_url,
            log10=False,
            selected_sites=selected_sites,
            tern_axes=tern_axes,                # NEW
            reference_url=reference_url,
        )
        return fig, ref_html


    @app.callback(
        Output('site-filter', 'options'),
        Output('site-filter', 'value'),
        Input('current-dataset-url', 'data'),
        Input('select-all-sites', 'n_clicks'),
        Input('unselect-all-sites', 'n_clicks')#,
        # prevent_initial_call=True
    )
    def update_site_filter(dataset_url, select_clicks, unselect_clicks):
        ctx = dash.callback_context
        triggered_id = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else 'current-dataset-url'

        result = get_data(dataset_url, reference_url, log10=True)
        df_data = result["data"]
        context_names = sorted(df_data['context_name'].dropna().unique().tolist())
        options = [{'label': name, 'value': name} for name in context_names]

        if triggered_id in ('select-all-sites', 'current-dataset-url'):
            return options, context_names
        elif triggered_id == 'unselect-all-sites':
            return options, []
        else:
            raise dash.exceptions.PreventUpdate


    @app.callback(
        Output('tern-site-filter', 'options'),
        Output('tern-site-filter', 'value'),
        Input('tern-current-dataset-url', 'data'),
        Input('tern-select-all-sites', 'n_clicks'),
        Input('tern-unselect-all-sites', 'n_clicks'),
    )
    def update_tern_site_filter(dataset_url, select_clicks, unselect_clicks):
        ctx = dash.callback_context
        triggered_id = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else 'tern-current-dataset-url'

        # Use same source as your other filter: data frame has context_name
        result = get_data(dataset_url, reference_url, log10=True)
        df_data = result["data"]
        context_names = sorted(df_data['context_name'].dropna().unique().tolist())
        options = [{'label': name, 'value': name} for name in context_names]

        if triggered_id in ('tern-select-all-sites', 'tern-current-dataset-url'):
            return options, context_names
        elif triggered_id == 'tern-unselect-all-sites':
            return options, []
        else:
            raise dash.exceptions.PreventUpdate


    @app.callback(
        Output('download-csv', 'data'),
        Input('download-csv-btn', 'n_clicks'),
        State('current-dataset-url', 'data'),
        State('current-slug', 'data'),
        prevent_initial_call=True
    )
    def download_csv(n_clicks, dataset_url, slug):
        result = get_data(dataset_url, reference_url, log10=True)
        df_data = result["data"]
        return dcc.send_data_frame(
            df_data.to_csv,
            f"chips_{slug}_data.csv",
            index=False
        )


    @app.callback(
        Output('tern-download-csv', 'data'),
        Input('tern-download-csv-btn', 'n_clicks'),
        State('tern-current-dataset-url', 'data'),
        State('tern-current-slug', 'data'),
        State('tern-site-filter', 'value'),
        prevent_initial_call=True
    )
    def download_tern_csv(n_clicks, dataset_url, slug, selected_sites):
        result = get_data(dataset_url, reference_url, log10=False)
        df_data = result["data"]

        if selected_sites:
            df_data = df_data[df_data["context_name"].isin(selected_sites)]

        return dcc.send_data_frame(
            df_data.to_csv,
            f"chips_{slug}_data.csv",
            index=False
        )


