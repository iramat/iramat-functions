import dash
from dash import dcc, html
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import requests
from charts import api_pg_dataset_linechart

# Fetch data once for this example (could be dynamic)
urls = {
    "dataset": "http://157.136.252.188:3000/dataset_adisser17",
    "reference": "http://157.136.252.188:3000/ref_elements"
}
result = api_pg_dataset_linechart(urls["dataset"], urls["reference"], log10=True)
df_log = result["elements"]

# Create the Dash app
# app = dash.Dash(__name__)
# app = dash.Dash(__name__, requests_pathname_prefix='/dash/')
app = dash.Dash(__name__)


# Build the line chart using Plotly
fig = go.Figure()
for idx, row in df_log.iterrows():
    fig.add_trace(go.Scatter(
        x=df_log.columns,
        y=row.values,
        mode='lines+markers',
        name=str(idx)
    ))

fig.update_layout(title="dataset_adisser17",
                  xaxis_title="Element",
                  yaxis_title="Log10 Value")

# App Layout
app.layout = html.Div([
    html.H1("CHIPS Dashboard"),
    dcc.Graph(figure=fig)
])

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=8050)
    # app.run(debug=False)

