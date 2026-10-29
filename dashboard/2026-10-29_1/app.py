from callbacks import register_callbacks

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


# customisation
coloramp_all_dataset_map='tab20b'

# assets_path = os.path.join(os.path.dirname(__file__), 'assets')

# web = False
# local = not web

tit = "CHIPS Dashboard"

df = read_data_urls(read_ref=False)
# print(type(df))

dataset_slugs = df['dataset_name']
dataset_nums = df['dataset_num']
dataset_map = dict(zip(dataset_slugs, df['url_data']))
dataset_map_nums = dict(zip(dataset_slugs, df['dataset_num']))
# avoiding '.0' in dataset numbers
# dataset_map_nums = dict(zip(dataset_slugs, [str(num).rstrip('.0') if '.0' in str(num) else str(num) for num in dataset_nums]))
# dataset_num = dataset_num.rstrip('.0') if '.0' in dataset_num else dataset_num
# print(dataset_map_nums)
# print(dataset_map_nums )
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


register_callbacks(app, df, dataset_slugs, dataset_map, dataset_map_nums, coloramp_all_dataset_map)

# ----------- RUN SERVER ---------------- #

debug = False # Set to True for debugging

if __name__ == '__main__':
    # app.run(debug=True, host='0.0.0.0', port=8050)
    app.run(debug=debug, host="127.0.0.1", port=8050)