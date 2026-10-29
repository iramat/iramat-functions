"""Dashboard pages and reusable chart-page components."""
from urllib.parse import parse_qs
from dash import dcc, html
from maps import generate_one_dataset, generate_all_datasets_map

CHART_VIEWS = (
    ("line", "Line Chart", lambda slug: f"/dash/{slug}"),
    ("scatter", "Scatter Plot", lambda slug: f"/dash/chartscatter/{slug}"),
    ("ternary", "Ternary Plot", lambda slug: f"/dash/charttern/{slug}"),
)


def chart_navigation(slug, current):
    """Navigation is shared by all three chart views."""
    return html.Ul([
        html.Li(html.A("🗺️ Map", href=f"/dash/mapview?dataset={slug}")),
        *[html.Li(html.Strong(label) if kind == current else html.A(label, href=url(slug)))
          for kind, label, url in CHART_VIEWS],
    ])


def context_filter(prefix):
    """Each view has its own component IDs, but identical controls."""
    return html.Div([
        html.H4("Filter by Context"),
        html.Button("Select All", id=f"{prefix}-select-all-sites", n_clicks=0,
                    style={"marginRight": "10px"}),
        html.Button("Unselect All", id=f"{prefix}-unselect-all-sites", n_clicks=0),
        html.Br(), html.Br(),
        dcc.Checklist(id=f"{prefix}-site-filter", options=[], value=[],
                      labelStyle={"display": "block"}, inputStyle={"marginRight": "10px"}),
    ])


def chart_controls(kind):
    if kind == "line":
        return dcc.RadioItems(id="line-scale-selector", options=[
            {"label": "Log Scale", "value": "log"},
            {"label": "Linear Scale", "value": "linear"}], value="log",
            labelStyle={"display": "inline-block", "marginRight": "12px"})
    if kind == "scatter":
        return html.Div([
            html.Label("Y-axis oxide (X-axis: FeO)"),
            dcc.RadioItems(id="scatter-y-selector", options=[
                {"label": "Al₂O₃", "value": "Al2O3"},
                {"label": "SiO₂", "value": "SiO2"}], value="Al2O3",
                labelStyle={"display": "inline-block", "marginRight": "16px"}),
        ])
    return dcc.RadioItems(id="ternary-axes-selector", options=[
        {"label": "FeO-SiO₂-Al₂O₃", "value": "FeO_SiO2_Al2O3"},
        {"label": "FeO-MnO-CaO", "value": "FeO_MnO_CaO"},
        {"label": "FeO-K₂O-P₂O₅", "value": "FeO_K2O_P2O5"}],
        value="FeO_SiO2_Al2O3", labelStyle={"display": "block", "marginBottom": "8px"})


def generate_chart_page(dataset_url, dataset_num, slug, kind):
    """One common page structure for line, scatter, and ternary plots."""
    prefix = kind
    title = next(label for key, label, _ in CHART_VIEWS if key == kind)
    return html.Div(style={"display": "flex", "height": "100vh"}, children=[
        html.Div(style={"width": "300px", "padding": "20px", "backgroundColor": "#f2f2f2",
                        "overflowY": "auto", "flexShrink": 0}, children=[
            html.A("⬅ Home", href="/dash/"),
            html.H3(f"Dataset {dataset_num} ({slug})"),
            chart_navigation(slug, kind),
            context_filter(prefix),
        ]),
        html.Div(style={"flex": "1", "minWidth": 0, "padding": "10px"}, children=[
            dcc.Store(id=f"{prefix}-current-dataset-url", data=dataset_url),
            dcc.Store(id=f"{prefix}-current-slug", data=slug),
            html.H3(title),
            html.Div(style={"display": "flex", "justifyContent": "space-between", "gap": "20px"}, children=[
                html.Div(chart_controls(kind), style={"flex": "1"}),
                html.Div(id=f"{prefix}-reference-info", style={"flex": "2"}),
            ]),
            dcc.Loading(type="default", children=dcc.Graph(id=f"{prefix}-graph")),
        ]),
    ])


def render_page(pathname, search, df, dataset_slugs, dataset_map, dataset_map_nums, coloramp_all_dataset_map):
# def display_page(pathname, search):
    # Remove '/dash/' prefix to isolate the slug
    path = (pathname or '').removeprefix('/dash/').strip('/')
    
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
        slug = parse_qs((search or '').lstrip('?')).get('dataset', [''])[0]
        if slug not in dataset_map:
            return html.Div([html.H2('404 - Page not found'), html.P('Unknown dataset')])
        
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
                    html.Li(html.A("◉ Scatter Plot", href=f"/dash/chartscatter/{slug}")),
                    html.Li(html.A("△ Ternary Plot", href=f"/dash/charttern/{slug}")),
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
        
    for prefix, kind in (("charttern/", "ternary"), ("chartscatter/", "scatter")):
        if path.startswith(prefix):
            slug = path[len(prefix):]
            if slug in dataset_map:
                return generate_chart_page(dataset_map[slug], dataset_map_nums[slug], slug, kind)
            return html.Div([html.H2("404 - Page not found"), html.P(f"No dataset found for: {slug}")])

    if path in dataset_map:
        return generate_chart_page(dataset_map[path], dataset_map_nums[path], path, "line")

    return html.Div([html.H2("404 - Page not found"), html.P(f"No dataset or route found for: {pathname}")])
