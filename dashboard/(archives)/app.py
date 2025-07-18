import dash
from dash import dcc, html, Input, Output
import plotly.graph_objects as go
import re
from charts import api_pg_dataset_linechart
from urls import read_data_urls

web = False
local = not web

tit="CHIPS Dashboard"

df = read_data_urls(read_ref=False)

# Extract slugs for URL routing
dataset_slugs = df['dataset_name']
dataset_map = dict(zip(dataset_slugs, df['url_data']))

# Initialize app
if(local):
    app = dash.Dash(__name__)
if(web):
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

def generate_dataset_page(dataset_url):
    result = api_pg_dataset_linechart(dataset_url, df["url_reference"], log10=True)
    df_log = result["elements"]
    df_data = result["data"]
    print(df_log.head())
    print(df_data.head())
    # x_vals = df_log.columns.astype(float)  # Convert column names to float

    fig = go.Figure()
    for idx, row in df_log.iterrows():
        fig.add_trace(go.Scatter(
            x=df_log.columns,
            y=row.values,
            mode='lines+markers',
            hovertemplate='elt: %{x}<br>val: %{y:.3f}<extra></extra>',
            name=df_data.loc[idx, 'site_name']
        ))

    dataset_name = re.search(r'[^/]+$', dataset_url).group()
    fig.update_layout(
    title=dict(
        text=f"Dataset: {dataset_name}",
        x=0.5,
        xanchor='left'
    ),
    xaxis_title="Element",
    yaxis_title="Log10 Value",
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

    # Layout with sidebar + main panel
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
                # html.Li(html.A(slug, href=f"/dash/{slug}")) for slug in dataset_slugs
            html.Ul([
                # different URLs depend on web vs local
                html.Li(html.A(slug, href=f"/dash/{slug}")) if(web) else html.Li(html.A(slug, href=f"/{slug}"))
                for slug in dataset_slugs
        ])
            ])
        ]),
        # Main content
        html.Div(style={
            'flex': '1',
            'padding': '20px'
        }, children=[
            html.H1(tit),
            dcc.Graph(figure=fig)
        ])
    ])

# Route Handler
@app.callback(Output('page-content', 'children'),
              Input('url', 'pathname'))
def display_page(pathname):

    if(local):
        slug = pathname.strip("/")
    if(web):
        slug = pathname.rsplit("/", 1)[-1]

    if slug in dataset_map:
        return generate_dataset_page(dataset_map[slug])
    else:
        return html.Div([
            html.H2("404 - Page not found"),
            html.P("Invalid dataset slug in URL.")
        ])

# Run server
if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=8050)
