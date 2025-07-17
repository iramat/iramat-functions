import dash
from dash import dcc, html, Input, Output, State
import plotly.graph_objects as go
import re
# from charts import api_pg_dataset_linechart
from get_data import get_data
from urls import read_data_urls

web = False
local = not web

tit = "CHIPS Dashboard"

df = read_data_urls(read_ref=False)
dataset_slugs = df['dataset_name']
dataset_map = dict(zip(dataset_slugs, df['url_data']))

# Initialize app
if local:
    app = dash.Dash(__name__)
if web:
    app = dash.Dash(
        __name__,
        requests_pathname_prefix='/dash/',
        routes_pathname_prefix='/dash/'
    )

app.title = tit
app._favicon = ("logo.ico")
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])

def create_figure(dataset_url, log10=True, selected_sites=None):
    result = get_data(dataset_url, df["url_reference"], log10=log10)
    df_elt = result["elements"]
    df_data = result["data"]
    df_data['label'] = df_data['site_name'] + " - " + df_data['sample_name']

    # HTML-safe reference string
    refbib = html.A(df_data.at[0, 'reference'], href=df_data.at[0, 'url'], target='_blank')

    fig = go.Figure()

    for idx, row in df_elt.iterrows():
        site = df_data.loc[idx, 'site_name']
        if selected_sites and site not in selected_sites:
            continue

        label = df_data.loc[idx, 'label']
        customdata = [[label] for _ in df_elt.columns]

        fig.add_trace(go.Scatter(
            x=df_elt.columns,
            y=row.values,
            mode='lines+markers',
            customdata=customdata,
            hovertemplate='%{customdata[0]}<br><b>elt</b>: %{x} | <b>val</b>: %{y:.3f}<extra></extra>',
            name=label
        ))

    # dataset_name = re.search(r'[^/]+$', dataset_url).group()
    y_title = "Log10 Value" if log10 else "Original Value"

    fig.update_layout(
        # title=dict(
        #     text=f"Dataset: {dataset_name}",
        #     x=0,
        #     xanchor='left'
        # ),
        xaxis_title="Element",
        yaxis_title=y_title
    )

    # HTML layout for references
    ref_html = html.Div([
        html.H4("Sources & References"),
        html.Ul([
            html.Li([
                html.Span("API (data source): "),
                html.A(dataset_url, href=dataset_url, target='_blank')
            ]),
            html.Li([
                html.Span("Data reference: "),
                refbib
            ])
        ])
    ], style={'marginTop': '20px'})

    return fig, ref_html


def generate_dataset_page(dataset_url):
    dataset_name = re.search(r'[^/]+$', dataset_url).group()
    return html.Div(style={'display': 'flex', 'height': '100vh'}, children=[

        # Sidebar: Dataset List
        html.Div(style={
            'width': '200px',
            'padding': '20px',
            'backgroundColor': '#f2f2f2',
            'overflowY': 'auto'
        }, children=[
            html.H2("Datasets"),
            html.Ul([
                html.Li(html.A(slug, href=f"/dash/{slug}")) if web else html.Li(html.A(slug, href=f"/{slug}"))
                for slug in dataset_slugs
            ])
        ]),

        # Sidebar: Site Checklist
        html.Div(style={
            'width': '300px',
            'padding': '20px',
            'backgroundColor': '#e6e6e6',
            'overflowY': 'auto'
        }, children=[
            html.H3("Filter by Site"),

            html.Button("Select All", id='select-all-sites', n_clicks=0, style={'marginRight': '10px'}),
            html.Button("Unselect All", id='unselect-all-sites', n_clicks=0),

            html.Br(), html.Br(),

            dcc.Checklist(
                id='site-filter',
                options=[],   # Populated dynamically
                value=[],     # All selected by default
                labelStyle={'display': 'block'},
                inputStyle={'margin-right': '10px'}
            )
        ]),
        html.Div(style={'flex': '1', 'padding': '20px'}, children=[

            # Wrap titles + references in a horizontal row
            html.Div(style={'display': 'flex', 'justifyContent': 'space-between'}, children=[

                # Left column: Title and controls
                html.Div(style={'flex': '2', 'paddingRight': '40px'}, children=[
                    html.H1(tit),
                    html.H2(f"Dataset: {dataset_name}", style={"marginBottom": "20px"}),
                    dcc.Store(id='current-dataset-url', data=dataset_url),
                    dcc.RadioItems(
                        id='scale-selector',
                        options=[
                            {'label': 'Log Scale', 'value': 'log'},
                            {'label': 'Linear Scale', 'value': 'linear'}
                        ],
                        value='log',
                        labelStyle={'display': 'inline-block', 'margin-right': '10px'}
                    ),
                ]),

                # Right column: Reference info
                html.Div(style={'flex': '2'}, children=[
                    html.Div(id='reference-info'),
                ])
            ]),

            # Graph goes below the 2-column block
            dcc.Graph(id='dataset-graph')
        ])

    #     # Main Content: Graph and controls
    #     html.Div(style={'display': 'flex', 'justifyContent': 'space-between'}, children=[
    #     # Left column: Title and controls       ²
    #     html.Div(style={'flex': '2', 'paddingRight': '40px'}, children=[
    #         html.H1(tit),
    #         html.H2(f"Dataset: {dataset_name}", style={"marginBottom": "20px"}),
    #         dcc.Store(id='current-dataset-url', data=dataset_url),
    #         dcc.RadioItems(
    #             id='scale-selector',
    #             options=[
    #                 {'label': 'Log Scale', 'value': 'log'},
    #                 {'label': 'Linear Scale', 'value': 'linear'}
    #             ],
    #             value='log',
    #             labelStyle={'display': 'inline-block', 'margin-right': '10px'}
    #         ),
    #     ]),
    #     # Right column: Reference info
    #     html.Div(style={'flex': '1'}, children=[
    #         html.Div(id='reference-info'),
    #     ])
    # ])
    # dcc.Graph(id='dataset-graph')
    ])


# ----------- CALLBACKS ---------------- #

@app.callback(
    Output('page-content', 'children'),
    Input('url', 'pathname')
)
def display_page(pathname):
    slug = pathname.strip("/") if local else pathname.rsplit("/", 1)[-1]
    if slug in dataset_map:
        return generate_dataset_page(dataset_map[slug])
    else:
        return html.Div([
            html.H2("404 - Page not found"),
            html.P("Invalid dataset slug in URL.")
        ])


# @app.callback(
#     Output('site-filter', 'options'),
#     Output('site-filter', 'value'),
#     Input('current-dataset-url', 'data')
# )
# def populate_site_filter(dataset_url):
#     # result = api_pg_dataset_linechart(dataset_url, df["url_reference"], log10=True)
#     result = get_data(dataset_url, df["url_reference"], log10=True)
#     df_data = result["data"]
#     site_names = df_data['site_name'].unique()
#     options = [{'label': name, 'value': name} for name in site_names]
#     return options, list(site_names)  # Select all by default


# @app.callback(
#     Output('dataset-graph', 'figure'),
#     Input('scale-selector', 'value'),
#     Input('current-dataset-url', 'data'),
#     Input('site-filter', 'value')
# )
# def update_graph(scale_mode, dataset_url, selected_sites):
#     log10 = scale_mode == 'log'
#     return create_figure(dataset_url, log10=log10, selected_sites=selected_sites)

@app.callback(
    Output('dataset-graph', 'figure'),
    Output('reference-info', 'children'),
    Input('scale-selector', 'value'),
    Input('current-dataset-url', 'data'),
    Input('site-filter', 'value')
)
def update_graph(scale_mode, dataset_url, selected_sites):
    log10 = scale_mode == 'log'
    fig, ref_html = create_figure(dataset_url, log10=log10, selected_sites=selected_sites)
    return fig, ref_html

# @app.callback(
#     Output('site-filter', 'value'),
#     Input('select-all-sites', 'n_clicks'),
#     Input('unselect-all-sites', 'n_clicks'),
#     State('site-filter', 'options'),
#     prevent_initial_call=True
# )
# def toggle_all_sites(select_clicks, unselect_clicks, options):
#     ctx = dash.callback_context

#     if not ctx.triggered:
#         raise dash.exceptions.PreventUpdate

#     triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]

#     if triggered_id == 'select-all-sites':
#         return [opt['value'] for opt in options]
#     elif triggered_id == 'unselect-all-sites':
#         return []
#     else:
#         raise dash.exceptions.PreventUpdate

@app.callback(
    Output('site-filter', 'options'),
    Output('site-filter', 'value'),
    Input('current-dataset-url', 'data'),
    Input('select-all-sites', 'n_clicks'),
    Input('unselect-all-sites', 'n_clicks'),
    prevent_initial_call=True
)
def update_site_filter(dataset_url, select_clicks, unselect_clicks):
    ctx = dash.callback_context
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else None

    # Always refresh the options based on the current dataset
    result = get_data(dataset_url, df["url_reference"], log10=True)
    df_data = result["data"]
    site_names = df_data['site_name'].unique()
    options = [{'label': name, 'value': name} for name in site_names]

    if triggered_id == 'select-all-sites' or triggered_id == 'current-dataset-url':
        # Select all sites (either by explicit click or when new dataset is loaded)
        return options, list(site_names)
    elif triggered_id == 'unselect-all-sites':
        return options, []
    else:
        raise dash.exceptions.PreventUpdate


# ----------- RUN SERVER ---------------- #

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=8050)
