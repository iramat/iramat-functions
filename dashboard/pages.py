import re
from dash import dcc, html
from maps import generate_one_dataset, generate_all_datasets_map

def generate_dataset_page(dataset_url, dataset_num, slug):
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
                html.A("⬅ Home", href="/dash/"),
                # html.H2(f"{dataset_name}", style={"marginBottom": "20px"}),
                html.H3(f"Dataset {dataset_num} ({dataset_name})", style={"marginBottom": "20px"}),
                html.Ul([
                    html.Li(html.A("🗺️ View Map", href=f"/dash/mapview?dataset={slug}")),
                    html.Li(html.A("△ View Ternary Plot", href=f"/dash/charttern/{slug}"))
                ]),

                html.H4("Filter by Context"),

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


def generate_dataset_page_ternary(dataset_url, dataset_num, slug):
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
            html.A("⬅ Home", href="/dash/"),
            html.H3(f"Dataset {dataset_num} ({dataset_name})", style={"marginBottom": "20px"}),
            html.Ul([
                html.Li(html.A("🗺️ View Map", href=f"/dash/mapview?dataset={slug}")),
                html.Li(html.A("📈 View Line Chart", href=f"/dash/{slug}")),
            ]),

            html.H4("Filter by Context"),

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


def render_page(pathname, search, df, dataset_slugs, dataset_map, dataset_map_nums, coloramp_all_dataset_map):
# def display_page(pathname, search):
    # Remove '/dash/' prefix to isolate the slug
    path = pathname.replace('/dash/', '').strip('/')
    
    if path == "" or path == "index":
        return html.Div(style={'display': 'flex'}, children=[
                html.Div(style={'width': '280px', 'padding': '20px', 'backgroundColor': '#f2f2f2'}, children=[
                # html.H2("Welcome"),
                html.Div([
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
                    ),
                    html.H2(" CHIPS Dashboard", style={"margin": "0", "marginRight": "10px", "marginLeft": "10px"}),
                    # html.A(
                    #     children=[
                    #         html.Img(
                    #             src="/dash/assets/logo-chips-round.png",
                    #             style={
                    #                 "height": "40px", # Adjusted to match H2 better
                    #                 "verticalAlign": "middle",
                    #             }
                    #         ),
                    #     ],
                    #     href="https://iramat.github.io/chips/",
                    #     target="_blank",
                    #     style={"display": "flex", "alignItems": "center"}
                    # )
                ], style={"display": "flex", "alignItems": "center"}),
                html.P([
                    "This dashboard helps exploring the public side of the ",
                    html.A(
                            "CHIPS Database",
                            href="https://iramat.github.io/chips/dashboard/", 
                            target="_blank",
                            # style={"textDecoration": "none", "color": "inherit"}  # Optional: adjust styling
                        ),
                    # html.A(
                    #     children=[
                    #         html.Img(
                    #             src="/dash/assets/app-github.png",
                    #             style={
                    #                 "height": "20px",
                    #                 "verticalAlign": "middle",
                    #                 "marginRight": "5px"
                    #             }
                    #         ),
                    #         ""
                    #     ],
                    #     href="https://iramat.github.io/chips/",
                    #     target="_blank",
                    #     style={"textDecoration": "none", "color": "black"}
                    # )
                ]),
                html.H3("Datasets"),
                # html.Ul([
                #     html.Li(html.A(slug, href=f"/dash/mapview?dataset={slug}")) for slug in dataset_slugs
                # ])
                # html.Ul([
                #     html.Li(
                #         html.A(
                #             f"CHIPS dataset {dataset_map_nums[slug].rstrip('.0')} ({slug})",
                #             href=f"/dash/mapview?dataset={slug}"
                #         )
                #     )
                #     for slug in dataset_slugs
                # ])
                # html.Div([
                #     html.A(
                #         f"CHIPS dataset {dataset_map_nums[slug]} ({slug})",
                #         href=f"/dash/mapview?dataset={slug}"
                #     ),
                #     html.Br()
                #     for slug in dataset_slugs
                # ])
                html.Ul(
                    [
                        html.Li(
                            html.A(
                                f"- Dataset {dataset_map_nums[slug]} ({slug})",
                                href=f"/dash/mapview?dataset={slug}"
                            )
                        )
                        for slug in dataset_slugs
                    ],
                    style={
                        "listStyleType": "none",
                        "paddingLeft": 0,
                        "marginLeft": 0,
                    },
                ),
                "Each dataset is a separate entity and can be cited individually, while the CHIPS database itself has another type of mention (see ",
                    html.A(
                        "How-to-cite",
                        href="https://iramat.github.io/chips/docs/#how-to-cite",  # Replace with the actual link
                        target="_blank",
                        # style={"textDecoration": "none", "color": "inherit"}  # Optional: adjust styling
                    ),
                    ")."
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
        dataset_num = str(dataset_map_nums.get(slug)) # num dataset
        # dataset_num = dataset_num.rstrip('.0') if '.0' in dataset_num else dataset_num
        # print(type(dataset_num), dataset_num)

        return html.Div(style={'display': 'flex'}, children=[
            html.Div(style={'width': '300px', 'padding': '20px', 'backgroundColor': '#f2f2f2'}, children=[
                html.P(html.A("⬅ Home", href="/dash/")),
                html.H3(f"Dataset {dataset_num} ({slug})"),
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
                # children=[generate_dataset_page_ternary(dataset_map[slug], slug)]
                children=[generate_dataset_page_ternary(dataset_map[slug], dataset_map_nums[slug], slug)]
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
                # generate_dataset_page(dataset_map[slug], slug)
                generate_dataset_page(dataset_map[slug], dataset_map_nums[slug], slug)
            ]
        )
    else:
        return html.Div([
        html.H2("404 - Page not found"),
        html.P(f"No dataset or route found for: {pathname}")
    ])

