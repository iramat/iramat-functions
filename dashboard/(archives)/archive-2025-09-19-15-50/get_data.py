# Function to get data from API
def safe_log10(x):
    import numpy as np
    try:
        val = float(x)
        return np.log10(val) if val > 0 else np.nan
    except (TypeError, ValueError):
        return np.nan
    
def get_data(url_dataset, url_reference_elements, log10=True):
    import pandas as pd
    import requests
    import numpy as np

    response_ref = requests.get(url_reference_elements)
    ref_elements = response_ref.json()
    ref = pd.DataFrame(ref_elements)

    response_data = requests.get(url_dataset)
    data = response_data.json()
    df = pd.DataFrame(data)

    # update refbib
    # df['linked_reference'] = df.apply(lambda row: f"<a href='{row['url']}' target='_blank'>{row['reference']}</a>", axis=1)

    # order df
    new_column_order = ref["symbole"].str.lower().tolist()
    ordered_df = df[[col for col in new_column_order if col in df.columns]]
    # print(type(new_column_order))

    if log10:
        # df_log10 = ordered_df.applymap(safe_log10)
        df_log10 = ordered_df.map(safe_log10)
    else:
        df_log10 = ordered_df
        
    # Capitalize elements symbols
    df.rename(columns={col: col.capitalize() for col in df.columns if col in new_column_order}, inplace=True)
    df_log10.rename(columns={col: col.capitalize() for col in df_log10.columns if col in new_column_order}, inplace=True)


    return {
        "data": df,
        "elements": df_log10
    }

# def api_pg_dataset_linechart(url_dataset, url_reference_elements, log10=True):
#     import pandas as pd
#     import requests
    
#     response_ref = requests.get(url_reference_elements)
#     ref_elements = response_ref.json()
#     ref = pd.DataFrame(ref_elements)

#     response_data = requests.get(url_dataset)
#     data = response_data.json()
#     df = pd.DataFrame(data)

#     new_column_order = ref["symbole"].str.lower().tolist()
#     ordered_df = df[[col for col in new_column_order if col in df.columns]]
    

#     if log10:
#         # df_log10 = ordered_df.applymap(safe_log10)
#         df_log10 = ordered_df.map(safe_log10)
#     else:
#         df_log10 = ordered_df
        
#     df.columns = [col.capitalize() for col in df.columns]
#     df_log10.columns = [col.capitalize() for col in df_log10.columns]

#     return {
#         "data": df,
#         "elements": df_log10
#     }