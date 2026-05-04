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
import plotly.express as px  # only for color palettes
import plotly.graph_objects as go
import re
import pandas as pd
# import folium
# from folium.plugins import MarkerCluster
# from shapely.geometry import MultiPoint
# import geopandas as gpd
from get_data import get_data
from urls import read_data_urls
from maps import generate_one_dataset
from maps import generate_all_datasets_map


# customisation
coloramp_all_dataset_map='tab20b'

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
        <link rel="icon" type="image/png" href="/dash/assets/logo-chips-round.png">
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
# app.layout = html.Div([
#     dcc.Location(id='url', refresh=False),
#     html.Div(
#         id='page-content',
#         style={
#             'display': 'flex',
#             'flexDirection': 'column',
#             'flex': '1',
#             'height': '100vh'   # full screen height
#         }
#     )
# ])
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),

    dcc.Loading(
        id="page-loading",
        type="default",   # "circle", "cube", "dot" also available
        children=html.Div(
            id='page-content',
            style={
                'display': 'flex',
                'flexDirection': 'column',
                'flex': '1',
                'height': '100vh'
            }
        )
    )
])

@app.callback(
    Output('page-content', 'children'),
    Input('url', 'pathname'),
    State('url', 'search')
)
def generate_dataset_map(pathname, search):
# def display_page(pathname, search):
    # Remove '/dash/' prefix to isolate the slug
    path = pathname.replace('/dash/', '').strip('/')
    
    if path == "" or path == "index":
        return html.Div(style={'display': 'flex'}, children=[
                html.Div(style={'width': '250px', 'padding': '20px', 'backgroundColor': '#f2f2f2'}, children=[
                # html.H2("Welcome"),
                html.Div([
                    html.H2("Welcome to CHIPS ", style={"margin": "0", "marginRight": "10px"}),
                    html.A(
                        children=[
                            html.Img(
                                src="/dash/assets/logo-chips-round.png",
                                style={
                                    "height": "40px", # Adjusted to match H2 better
                                    "verticalAlign": "middle",
                                }
                            ),
                        ],
                        href="https://iramat.github.io/chips/",
                        target="_blank",
                        style={"display": "flex", "alignItems": "center"}
                    )
                ], style={"display": "flex", "alignItems": "center"}),
                html.P([
                        "This dashboard helps exploring the CHIPS Database. Only a part of the whole database is made public. See also ",
                        # html.A("GitHub", 
                        #        href="https://github.com/iramat/chips",
                        #        target="_blank")
                        html.A(
                            children=[
                                html.Img(
                                    src="/dash/assets/app-github.png",
                                    style={
                                        "height": "20px",
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
            html.Div(style={'flex': '1', 'padding': '20px', 'height': '90vh'}, children=[
                generate_all_datasets_map(df = df, dataset_map = dataset_map, dataset_slugs = dataset_slugs, coloramp=coloramp_all_dataset_map)
            ]),
            # Right panel (NEW)
            html.Div(
                style={
                    "width": "220px",
                    "padding": "20px",
                    "backgroundColor": "#f7f7f7",
                    "borderLeft": "1px solid #ddd",
                },
                children=[
                    html.H4("Overview"),
                    html.Div([
                        html.Strong("Datasets: "), 
                        f"{len(dataset_slugs):,}",
                        # TODO: total samples and columns across all datasets?
                        # html.Br(),
                        # html.Strong("Columns: "),
                        # f"{len(df.columns) if hasattr(df, 'columns') else len(df.keys()):,}",
                    ]),
                ],
            )

            # html.Div(
            #     style={
            #         "width": "220px",
            #         "padding": "20px",
            #         "backgroundColor": "#f7f7f7",
            #         "borderLeft": "1px solid #ddd",
            #     },
            #     children=[
            #         html.H4("Overview"),
            #         html.Div([
            #             html.Strong("Datasets: "), f"{len(df):,}",
            #             html.Br(),
            #             html.Strong("Columns: "), f"{len(df.columns)}",
            #         ]),
            #     ],
            # )
        ])

    if path == "mapview" and search:
        # for each dataset
        slug = search.split('=')[-1]
        
        # HERE
        dataset_url = dataset_map.get(slug) # Data:

        return html.Div(style={'display': 'flex'}, children=[
            html.Div(style={'width': '200px', 'padding': '20px', 'backgroundColor': '#f2f2f2'}, children=[
                html.H2("CHIPS Dataset"),
                html.P(html.A("🏠 Back to Home", href="/dash/")),
                # html.Hr(),
                html.H3(f"{slug}"),
                html.Ul([
                    html.H3("Data"),
                    
                    # HERE
                    
                    html.Li(html.A("API", href=dataset_url, target="_blank")),
                    html.Li(html.A("CSV", id="map-download-csv-btn", n_clicks=0, href="#")),
                    # dcc.Download(id="tern-download-csv"),   
                    dcc.Store(id="map-current-dataset-url", data=dataset_url),
                    dcc.Store(id="map-current-slug", data=slug),
                    dcc.Download(id="map-download-csv"),
                    
                    ##
                    
                    html.Li(html.A("📈 Line Chart", href=f"/dash/{slug}")),
                    html.Li(html.A("△ Ternary Plot", href=f"/dash/charttern/{slug}")), # TODO
                ])
            ]),
            html.Div(style={'flex': '1', 'padding': '20px', 'height': '90vh'}, children=[
                html.H3(slug),
                # html.A("📈 Line Chart", href=f"/dash/{slug}"), html.Span(" | "), html.A("△ Ternary Plot", href=f"/dash/charttern/{slug}"), # TODO
                generate_one_dataset(df, slug, dataset_map)
            ]),
            # RIGHT stats panel (NEW)
            html.Div(
                style={
                    "width": "220px",
                    "padding": "20px",
                    "backgroundColor": "#f7f7f7",
                    "borderLeft": "1px solid #ddd"
                },
                children=[
                    html.H4("Dataset info"),
                    html.Div("Loading…", id="map-row-count"),
                ]

                # children=[
                #     html.H4("Dataset info"),
                #     html.Div("Loading…", id="map-row-count"),
                #     dcc.Store(id="map-current-dataset-url", data=dataset_url)
                # ]
            )
        ])
        
    # --- Ternary chart view: /dash/charttern/<slug> ---
    if path.startswith("charttern/"):
        slug = path.split("/", 1)[1]
        if slug in dataset_map:
            return html.Div(
                style={'flex': '1', 'padding': '20px'},
                children=[generate_dataset_page_ternary(dataset_map[slug], slug)]
            )
        return html.Div([
            html.H2("404 - Page not found"),
            html.P(f"No dataset found for: {slug}")
        ])
    
    elif path in dataset_map:
        # Chart view
        slug = path
        return html.Div(
            style={'flex': '1', 'padding': '20px'},
            children=[
                generate_dataset_page(dataset_map[slug], slug)
            ]
        )
    else:
        return html.Div([
        html.H2("404 - Page not found"),
        html.P(f"No dataset or route found for: {pathname}")
    ])
        
@app.callback(
    Output("map-row-count", "children"),
    Input("map-current-dataset-url", "data")
)
def update_map_row_count(dataset_url):
    if not dataset_url:
        return ""

    result = get_data(dataset_url, df["url_reference"], log10=False)
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
    result = get_data(dataset_url, df["url_reference"], log10=False)
    df_data = result["data"]
    return dcc.send_data_frame(
        df_data.to_csv,
        f"chips_{slug}_data.csv",
        index=False
    )


def create_figure_linechart(dataset_url, log10=True, selected_sites=None):
    result = get_data(dataset_url, df["url_reference"], log10=log10)
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

def create_figure_ternary(dataset_url, log10=False, selected_sites=None, tern_axes="FeO_SiO2_Al2O3"):
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

    result = get_data(dataset_url, df["url_reference"], log10=log10)
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


def generate_dataset_page(dataset_url, slug):
    """Generate the Line Chart view of a dataset"""
    dataset_name = re.search(r'[^/]+$', dataset_url).group()
    return html.Div(style={'display': 'flex', 'height': '100vh'}, children=[

        # Sidebar: Site Checklist
        html.Div(style={
            'width': '300px',
            'padding': '20px',
            'backgroundColor': '#f2f2f2',
            'overflowY': 'auto'
        }, 
        children=[
                html.A("🏠 Back to Home", href="/dash/"),
                html.H2(f"{dataset_name}", style={"marginBottom": "20px"}),
                html.Ul([
                    # html.Li(html.A("🏠 Back to Home", href="/dash/")),
                    html.Li(html.A("🗺️ View Map", href=f"/dash/mapview?dataset={slug}")),
                    html.Li(html.A("△ View Ternary Plot", href=f"/dash/charttern/{slug}"))
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
        html.Div(style={'flex': '1', 'padding': '10px'}, children=[

            # Wrap titles + references in a horizontal row
            html.Div(style={'display': 'flex', 'justifyContent': 'space-between'}, children=[

                # Left column: Title and controls
                html.Div(style={'flex': '1', 'paddingRight': '20px'}, children=[
                    # html.H1(tit),
                    # html.H3(f"{dataset_name}", style={"marginBottom": "20px"}),
                    dcc.Store(id='current-dataset-url', data=dataset_url),
                    dcc.Store(id="current-slug", data=slug),
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
                
                # Middle column: CSV download
                # html.Div(style={'paddingRight': '20px'}, children=[
                #     html.Button(
                #         "⬇ Download CSV",
                #         id='download-csv-btn',
                #         n_clicks=0,
                #         style={'marginBottom': '10px'}
                #     ),
                #     dcc.Download(id='download-csv')
                # ]),

                # Right column: Reference info
                html.Div(style={'flex': '2'}, children=[
                    html.Div(id='reference-info'),
                ])
            ]),

            # Graph goes below the 2-column block
            # dcc.Graph(id='dataset-graph')
            dcc.Loading(
                type="default",
                children=dcc.Graph(id='dataset-graph')
            )
        ])
    ])

def generate_dataset_page_ternary(dataset_url, slug):
    """Generate the Ternary Chart view of a dataset"""
    dataset_name = re.search(r'[^/]+$', dataset_url).group()

    return html.Div(style={'display': 'flex', 'height': '100vh'}, children=[

        # Sidebar: Site Checklist
        html.Div(style={
            'width': '300px',
            'padding': '20px',
            'backgroundColor': '#f2f2f2',
            'overflowY': 'auto'
        },
        children=[
            html.A("🏠 Back to Home", href="/dash/"),
            html.H3(f"{dataset_name}", style={"marginBottom": "20px"}),
            html.Ul([
                # html.Li(html.A("🏠 Back to Home", href="/dash/")),
                html.Li(html.A("🗺️ View Map", href=f"/dash/mapview?dataset={slug}")),
                html.Li(html.A("📈 View Line Chart", href=f"/dash/{slug}")),
            ]),

            html.H3("Filter by Site"),

            html.Button("Select All", id='tern-select-all-sites', n_clicks=0, style={'marginRight': '10px'}),
            html.Button("Unselect All", id='tern-unselect-all-sites', n_clicks=0),

            html.Br(), html.Br(),

            dcc.Checklist(
                id='tern-site-filter',
                options=[],
                value=[],
                labelStyle={'display': 'block'},
                inputStyle={'margin-right': '10px'}
            )
        ]),

        # Main Content
        html.Div(style={'flex': '1', 'padding': '10px'}, children=[

            html.Div(style={'display': 'flex', 'justifyContent': 'space-between'}, children=[

                # # Left: title + store
                html.Div(style={'flex': '1', 'paddingRight': '20px'}, children=[
                    # html.H3(f"{dataset_name}", style={"marginBottom": "20px"}),
                    dcc.Store(id='tern-current-dataset-url', data=dataset_url),
                    dcc.Store(id="tern-current-slug", data=slug),
                    dcc.RadioItems(
                        id="tern-axes-selector",
                        options=[
                            {"label": "FeO-SiO2-Al2O3", "value": "FeO_SiO2_Al2O3"},
                            {"label": "FeO-MnO-CaO", "value": "FeO_MnO_CaO"},
                            {"label": "FeO-K2O-P2O5", "value": "FeO_K2O_P2O5"},
                        ],
                        value="FeO_SiO2_Al2O3",  # default
                        labelStyle={"display": "block", "marginBottom": "10px"},
                    ),
                ]),

                # # Middle: CSV download of *selected sites data* (optional)
                # html.Div(style={'paddingRight': '20px'}, children=[
                #     html.Button(
                #         "⬇ Download CSV",
                #         id='tern-download-csv-btn',
                #         n_clicks=0,
                #         style={'marginBottom': '10px'}
                #     ),
                #     dcc.Download(id='tern-download-csv')
                # ]),

                # Right: references
                html.Div(style={'flex': '2'}, children=[
                    html.Div(id='tern-reference-info'),
                ])
            ]),
            dcc.Loading(
                type="default",
                children=dcc.Graph(id='ternary-graph')
            )
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
    """Update the linechart"""
    log10 = scale_mode == 'log'
    fig, ref_html = create_figure_linechart(dataset_url, log10=log10, selected_sites=selected_sites)
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

    result = get_data(dataset_url, df["url_reference"], log10=True)
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
    result = get_data(dataset_url, df["url_reference"], log10=True)
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
    result = get_data(dataset_url, df["url_reference"], log10=True)
    df_data = result["data"]
    return dcc.send_data_frame(
        df_data.to_csv,
        f"chips_{slug}_data.csv",
        index=False
    )

# @app.callback(
#     Output('download-csv', 'data'),
#     Input('download-csv-btn', 'n_clicks'),
#     State('current-dataset-url', 'data'),
#     prevent_initial_call=True
# )
# def download_csv(n_clicks, dataset_url):
#     # Recompute df_data from the same source used in create_figure_linechart
#     result = get_data(dataset_url, df["url_reference"], log10=True)
#     df_data = result["data"]
#     # Export df_data as CSV
#     return dcc.send_data_frame(df_data.to_csv, "chips_dataset.csv", index=False)

# @app.callback(
#     Output('tern-download-csv', 'data'),
#     Input('tern-download-csv-btn', 'n_clicks'),
#     State('tern-current-dataset-url', 'data'),
#     State('tern-site-filter', 'value'),
#     prevent_initial_call=True
# )
# def download_tern_csv(n_clicks, dataset_url, selected_sites):
#     result = get_data(dataset_url, df["url_reference"], log10=False)
#     df_data = result["data"]

#     if selected_sites:
#         df_data = df_data[df_data["context_name"].isin(selected_sites)].copy()

#     return dcc.send_data_frame(df_data.to_csv, "chips_ternary_data.csv", index=False)
@app.callback(
    Output('tern-download-csv', 'data'),
    Input('tern-download-csv-btn', 'n_clicks'),
    State('tern-current-dataset-url', 'data'),
    State('tern-current-slug', 'data'),
    State('tern-site-filter', 'value'),
    prevent_initial_call=True
)
def download_tern_csv(n_clicks, dataset_url, slug, selected_sites):
    result = get_data(dataset_url, df["url_reference"], log10=False)
    df_data = result["data"]

    if selected_sites:
        df_data = df_data[df_data["context_name"].isin(selected_sites)]

    return dcc.send_data_frame(
        df_data.to_csv,
        f"chips_{slug}_data.csv",
        index=False
    )


# ----------- RUN SERVER ---------------- #

debug = True # Set to True for debugging

if __name__ == '__main__':
    # app.run(debug=True, host='0.0.0.0', port=8050)
    app.run(debug=debug, host="127.0.0.1", port=8051)