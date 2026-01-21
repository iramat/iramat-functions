import dash
from dash import dcc, html, Input, Output
import plotly.graph_objects as go
import re
from charts import api_pg_dataset_linechart
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
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])


# ----------- FIGURE CREATION FUNCTION ---------------- #
def create_figure(dataset_url, log10=True):
    result = api_pg_dataset_linechart(dataset_url, df["url_reference"], log10=log10)
    df_elt = result["elements"]
    df_data = result["data"]
    df_data['label'] = df_data['site_name'] + " - " + df_data['sample_name'] 

    fig = go.Figure()

    for idx, row in df_elt.iterrows():
        label = df_data.loc[idx, 'label']

        # Repeat the same label for every x value (so customdata aligns with each point)
        customdata = [[label] for _ in df_elt.columns]

        fig.add_trace(go.Scatter(
            x=df_elt.columns,
            y=row.values,
            mode='lines+markers',
            customdata=customdata,
            hovertemplate='%{customdata[0]}<br><b>elt</b>: %{x} | <b>val</b>: %{y:.3f}<extra></extra>',
            name=label
        ))

    dataset_name = re.search(r'[^/]+$', dataset_url).group()
    y_title = "Log10 Value" if log10 else "Original Value"
    # y_type = "log" if log10 else "linear"

    fig.update_layout(
        title=dict(
            text=f"Dataset: {dataset_name}",
            x=0.5,
            xanchor='left'
        ),
        xaxis_title="Element",
        yaxis_title=y_title,
        # yaxis_type=y_type,
        annotations=[
            dict(
                text=f"API (data source): <a href='{dataset_url}' target='_blank'>{dataset_url}</a>",
                x=0.5,
                y=1.05,
                xref='paper',
                yref='paper',
                showarrow=False,
                font=dict(size=14),
                align='left'
            )
        ]
    )
    return fig


# ----------- PAGE LAYOUT FUNCTION ---------------- #
def generate_dataset_page(dataset_url):
    return html.Div(style={'display': 'flex', 'height': '100vh'}, children=[
        # Sidebar
        html.Div(style={
            'width': '250px',
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

        # Main Content
        html.Div(style={
            'flex': '1',
            'padding': '20px'
        }, children=[
            html.H1(tit),
            dcc.RadioItems(
                id='scale-selector',
                options=[
                    {'label': 'Log Scale', 'value': 'log'},
                    {'label': 'Linear Scale', 'value': 'linear'}
                ],
                value='log',
                labelStyle={'display': 'inline-block', 'margin-right': '10px'}
            ),
            dcc.Store(id='current-dataset-url', data=dataset_url),
            dcc.Graph(id='dataset-graph')
        ])
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


@app.callback(
    Output('dataset-graph', 'figure'),
    Input('scale-selector', 'value'),
    Input('current-dataset-url', 'data')
)
def update_graph(scale_mode, dataset_url):
    log10 = scale_mode == 'log'
    return create_figure(dataset_url, log10=log10)


# ----------- RUN SERVER ---------------- #

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=8050)
