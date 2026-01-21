import dash
from dash import dcc, html, Input, Output
import plotly.graph_objects as go
import re
from charts import api_pg_dataset_linechart
from urls import read_data_urls

df = read_data_urls(read_ref=False)

# Extract slugs for URL routing
dataset_slugs = df['dataset_name']
dataset_map = dict(zip(dataset_slugs, df['url_data']))

# Initialize app
app = dash.Dash(
    __name__,
    requests_pathname_prefix='/dash/',
    routes_pathname_prefix='/dash/'
)
app.title = "Dynamic Dataset Viewer"

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])

def generate_dataset_page(dataset_url):
    result = api_pg_dataset_linechart(dataset_url, df["url_reference"], log10=True)
    df_log = result["elements"]
    df_data = result["data"]

    fig = go.Figure()
    for idx, row in df_log.iterrows():
        fig.add_trace(go.Scatter(
            x=df_log.columns,
            y=row.values,
            mode='lines+markers',
            name=df_data.loc[idx, 'site_name']
        ))

    fig.update_layout(
        title=f"Dataset: {re.search(r'[^/]+$', dataset_url).group()}",
        xaxis_title="Element",
        yaxis_title="Log10 Value"
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
                html.Li(html.A(slug, href=f"/{slug}")) for slug in dataset_slugs
            ])
        ]),

        # Main content
        html.Div(style={
            'flex': '1',
            'padding': '20px'
        }, children=[
            html.H1("CHIPS Dashboard"),
            dcc.Graph(figure=fig)
        ])
    ])

# Route Handler
@app.callback(Output('page-content', 'children'),
              Input('url', 'pathname'))
def display_page(pathname):
    slug = pathname.strip("/")

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
