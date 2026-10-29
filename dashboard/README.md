# CHIPS Dashboard refactor

This refactor was made from the two uploaded files only. Keep your existing `get_data.py`, `urls.py`, `maps.py`, and `assets/` unchanged in the same folder.

- `app.py`: app initialization, dataset metadata, root layout, callback registration, server startup.
- `pages.py`: page rendering and Dash HTML layouts.
- `charts.py`: Plotly chart construction and element-to-oxide conversion.
- `callbacks.py`: Dash callbacks, including CSV downloads and filters.

Before replacing your originals, back them up and test the homepage, map, line chart, ternary chart, filters, and CSV downloads. This is a structural refactor, not a tested deployment: the other project modules and live APIs were not supplied.

Run from the dashboard folder with `python app.py`. The port in the uploaded file is 8050; adjust if your current local setup uses 8052.
