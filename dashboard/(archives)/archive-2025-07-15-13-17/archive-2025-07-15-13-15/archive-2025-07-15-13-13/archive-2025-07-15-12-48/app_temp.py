import dash
from dash import dcc, html
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import requests

# Your safe log10 function
def safe_log10(x):
    try:
        val = float(x)
        return np.log10(val) if val > 0 else np.nan
    except (TypeError, ValueError):
        return np.nan

# Function to get data from API
def api_pg_dataset_linechart(url_dataset, url_reference_elements, log10=True):
    response_ref = requests.get(url_reference_elements)
    ref_elements = response_ref.json()
    ref = pd.DataFrame(ref_elements)

    response_data = requests.get(url_dataset)
    data = response_data.json()
    df = pd.DataFrame(data)

    new_column_order = ref["symbole"].str.lower().tolist()
    ordered_df = df[[col for col in new_column_order if col in df.columns]]

    if log10:
        df_log10 = ordered_df.applymap(safe_log10)
    else:
        df_log10 = ordered_df

    return {
        "data": df,
        "elements": df_log10
    }

# Fetch data once for this example (could be dynamic)
urls = {
    "dataset": "http://157.136.252.188:3000/dataset_adisser17",
    # "dataset": ['http://157.136.252.188:3000/dataset_tyoungxx', 'http://157.136.252.188:3000/dataset_adisser17'],
    "reference": "http://157.136.252.188:3000/ref_elements"
}
result = api_pg_dataset_linechart(urls["dataset"][0], urls["reference"], log10=True)
df_log = result["elements"]

# Create the Dash app
# app = dash.Dash(__name__)
app = dash.Dash(__name__, requests_pathname_prefix='/dash/')


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

