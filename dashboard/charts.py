# Function to get data from API
def safe_log10(x):

    import numpy as np
    try:
        val = float(x)
        return np.log10(val) if val > 0 else np.nan
    except (TypeError, ValueError):
        return np.nan

def api_pg_dataset_linechart(url_dataset, url_reference_elements, log10=True, order_atom_num=True):
    """
    Function used to plot chemical data hosted on the API as a linechart used to compare profiles and identify possible chemical anomalies ; 

    :param url_dataset: url of the dataset used to display the chemical data
    :param url_reference_elements: url to the reference table listing all known chemical elements and their main properties
    :param log10: boolean; if true, decimal logarithm is computed from raw data. Used to compare data present in distinct orders of magnitude
    
    >>> importing the reference table of chemical elements as a dataframe
    >>> response_ref = requests.get(url_reference_elements)
    >>> ref_elements = response_ref.json()
    >>> ref = pd.DataFrame(ref_elements)

    >>> importing the dataset to be examined as a dataframe
    >>> response_data = requests.get(url_dataset)
    >>> data = response_data.json()
    >>> df = pd.DataFrame(data)
    """
    import pandas as pd
    import requests
    
    response_ref = requests.get(url_reference_elements)
    ref_elements = response_ref.json()
    ref = pd.DataFrame(ref_elements)

    response_data = requests.get(url_dataset)
    data = response_data.json()
    df = pd.DataFrame(data)

    ref_column = ref["symbole"].str.lower().tolist()
    print(type(ref_column))

    if order_atom_num:
        ordered_df = df[[col for col in ref_column if col in df.columns]]
    else:
        column_subset = list(df.columns.intersection(ref_column))
        print(column_subset)
        ordered_df = df[column_subset]
    

    if log10:
        df_log10 = ordered_df.applymap(safe_log10)
    else:
        df_log10 = ordered_df
    
    return {
        "data": df,
        "elements": df_log10
    }