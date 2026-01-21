# Bulk upload of the dash functions
# in the VM:
#   - run './_upload_from_gh.sh' to upload the updated functions from GitHub. 
#   - after what, remember to update the app.py with the appropriate app name:
#   """
#   app = dash.Dash(
#     __name__,
#     requests_pathname_prefix='/dash/',
#     routes_pathname_prefix='/dash/'
#   )
#   """
#   - set `web = False`

# import os
import dash
from dash import dcc, html, Input, Output, State
import plotly.graph_objects as go
import re
# import pandas as pd
import folium
from folium.plugins import MarkerCluster
from shapely.geometry import MultiPoint
import geopandas as gpd
from get_data import get_data
from urls import read_data_urls
from maps import generate_map_view
from maps import generate_all_datasets_map


# assets_path = os.path.join(os.path.dirname(__file__), 'assets')

# web = False
# local = not web

tit = "CHIPS Dashboard"

df = read_data_urls(read_ref=False)
dataset_slugs = df['dataset_name']
dataset_map = dict(zip(dataset_slugs, df['url_data']))

# # Initialize app
app = dash.Dash(
    __name__,
    # assets_folder=assets_path,
    requests_pathname_prefix='/dash/',
    routes_pathname_prefix='/dash/',
    suppress_callback_exceptions=True
)

app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        <link rel="icon" type="image/png" href="/dash/assets/logo.png">
        {%css%}
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

app.title = tit
# app.favicon = ("logo.ico")
# app.layout = html.Div([
#     dcc.Location(id='url', refresh=False),
#     html.Div(id='page-content')
# ])
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(
        id='page-content',
        style={
            'display': 'flex',
            'flexDirection': 'column',
            'flex': '1',
            'height': '100vh'   # full screen height
        }
    )
])


@app.callback(
    Output('page-content', 'children'),
    Input('url', 'pathname'),
    State('url', 'search')
)
def display_page(pathname, search):
    # Remove '/dash/' prefix to isolate the slug
    path = pathname.replace('/dash/', '').strip('/')
    
    if path == "" or path == "index":
        return html.Div(style={'display': 'flex'}, children=[
                html.Div(style={'width': '250px', 'padding': '20px', 'backgroundColor': '#f2f2f2'}, children=[
                html.H2("Welcome"),
                html.P([
                        "This dashboard helps Exploring The CHIPS Database. See also ",
                        # html.A("GitHub", 
                        #        href="https://github.com/iramat/chips",
                        #        target="_blank")
                        html.A(
                            children=[
                                html.Img(
                                    src="/dash/assets/app-github.png",
                                    style={
                                        "height": "25px",
                                        "verticalAlign": "middle",
                                        "marginRight": "5px"
                                    }
                                ),
                                ""
                            ],
                            href="https://github.com/iramat/chips",
                            target="_blank",
                            style={"textDecoration": "none", "color": "black"}
                        )
                    ]),
                html.H3("Datasets"),
                html.Ul([
                    html.Li(html.A(slug, href=f"/dash/mapview?dataset={slug}")) for slug in dataset_slugs
                ])
            ]),
            html.Div(style={'flex': '1', 'padding': '20px'}, children=[
                generate_all_datasets_map(df = df, dataset_map = dataset_map, dataset_slugs = dataset_slugs)
            ])
        ])

    # if path == "" or path == "index":
    #     return html.Div(style={'display': 'flex'}, children=[
    #             html.Div(style={'width': '250px', 'padding': '20px', 'backgroundColor': '#f2f2f2'}, children=[
    #             html.H2("Welcome"),
    #             html.P([
    #                     "This dashboard helps exploring the CHIPS database. See also: ",
    #                     html.A("GitHub", 
    #                            href="https://github.com/iramat/iramat-dev/tree/main/dbs/chips",
    #                            target="_blank")
    #                 ]),
    #             html.H3("Datasets"),
    #             html.Ul([
    #                 html.Li(html.A(slug, href=f"/dash/mapview?dataset={slug}")) for slug in dataset_slugs
    #             ])
    #         ]),
    #         html.Div(style={'flex': '1', 'padding': '20px'}, children=[
    #             generate_all_datasets_map(df = df, dataset_map = dataset_map, dataset_slugs = dataset_slugs)
    #         ])
    #     ])

    if path == "mapview" and search:
        slug = search.split('=')[-1]
        return html.Div(style={'display': 'flex'}, children=[
            html.Div(style={'width': '200px', 'padding': '20px', 'backgroundColor': '#f2f2f2'}, children=[
                html.H2("Dataset List"),
                html.Ul([
                    html.Li(html.A("🏠 Back to Home", href="/dash/")),
                    html.Li(html.A("📈 View Line Chart", href=f"/dash/{slug}")),
                    html.Hr(),
                    *[
                        html.Li(html.A(s, href=f"/dash/mapview?dataset={s}"))
                        for s in dataset_slugs
                    ]
                ])
            ]),
            html.Div(style={'flex': '1', 'padding': '20px'}, children=[
                generate_map_view(df, slug, dataset_map)
            ])
        ])


    # if path == "dataset" and search:
    #     # Useful? seems never accessed...
    #     slug = search.split('=')[-1]
    #     return html.Div(style={'display': 'flex'}, children=[
    #         html.Div(style={'width': '200px', 'padding': '20px', 'backgroundColor': '#f2f2f2'}, children=[
    #             html.H1(tit),
    #             html.H2("Dataset List"),
    #             html.Ul([
    #                 html.Li(html.A("🏠 Back to HOME", href="/dash/")),
    #                 html.Li(html.A("🗺️ View Map", href=f"/dash/mapview?dataset={slug}")),
    #                 html.Hr(),
    #                 *[
    #                     html.Li(html.A(s, href=f"/dash/{s}")) for s in dataset_slugs
    #                 ]
    #             ])
    #         ]),
    #         html.Div(style={'flex': '1', 'padding': '20px'}, children=[
    #             generate_dataset_page(dataset_map[slug], slug)
    #         ])
    #     ])
    
    elif path in dataset_map:
        # Chart view
        slug = path
        return html.Div(
            style={'flex': '1', 'padding': '20px'},
            children=[
                # html.Div(
                #     # style={
                #     #     'backgroundColor': '#f2f2f2',  # light grey background
                #     #     'padding': '10px',
                #     #     'borderRadius': '5px',
                #     #     'marginBottom': '15px'
                #     # },
                #     children=[
                #         html.Ul([
                #             html.Li(html.A("🏠 Back to HoMe", href="/dash/")),
                #             html.Li(html.A("🗺️ View Map", href=f"/dash/mapview?dataset={slug}"))
                #         ])
                #     ]
                # ),
                generate_dataset_page(dataset_map[slug], slug)
            ]
        )
    else:
        return html.Div([
        html.H2("404 - Page not found"),
        html.P(f"No dataset or route found for: {pathname}")
    ])

def create_figure(dataset_url, log10=True, selected_sites=None):
    result = get_data(dataset_url, df["url_reference"], log10=log10)
    df_elt = result["elements"]
    df_data = result["data"]
    df_data['label'] = '<b>' + df_data['site_name'] + '</b>' + " - " + df_data['sample_name']

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


def generate_dataset_page(dataset_url, slug):
    dataset_name = re.search(r'[^/]+$', dataset_url).group()
    return html.Div(style={'display': 'flex', 'height': '100vh'}, children=[

        # Sidebar: Site Checklist
        html.Div(style={
            'width': '300px',
            'padding': '20px',
            'backgroundColor': '#f2f2f2',
            'overflowY': 'auto'
        }, 
        # children=[
        #     html.H3("Filter by Site"),

        #     html.Button("Select All", id='select-all-sites', n_clicks=0, style={'marginRight': '10px'}),
        #     html.Button("Unselect All", id='unselect-all-sites', n_clicks=0),

        #     html.Br(), html.Br(),

        #     dcc.Checklist(
        #         id='site-filter',
        #         options=[],   # Populated dynamically
        #         value=[],     # All selected by default
        #         labelStyle={'display': 'block'},
        #         inputStyle={'margin-right': '10px'}
        #     )
        # ]),
        children=[
                html.Ul([
                    html.Li(html.A("🏠 Back to HoMe", href="/dash/")),
                    html.Li(html.A("🗺️ View Map", href=f"/dash/mapview?dataset={slug}"))
                ]),

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


        # Main Content: Graph and controls
        html.Div(style={'flex': '1', 'padding': '20px'}, children=[

            # Wrap titles + references in a horizontal row
            html.Div(style={'display': 'flex', 'justifyContent': 'space-between'}, children=[

                # Left column: Title and controls
                html.Div(style={'flex': '1', 'paddingRight': '20px'}, children=[
                    # html.H1(tit),
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
    ])

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

    result = get_data(dataset_url, df["url_reference"], log10=True)
    df_data = result["data"]
    site_names = sorted(df_data['site_name'].dropna().unique().tolist())
    options = [{'label': name, 'value': name} for name in site_names]

    if triggered_id in ('select-all-sites', 'current-dataset-url'):
        return options, site_names
    elif triggered_id == 'unselect-all-sites':
        return options, []
    else:
        raise dash.exceptions.PreventUpdate

# ----------- RUN SERVER ---------------- #

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8050)
    # app.run(debug=True, host="127.0.0.1", port=8051)
