# Function to get data from API
def safe_log10(x):
    import numpy as np
    try:
        val = float(x)
        return np.log10(val) if val > 0 else np.nan
    except (TypeError, ValueError):
        return np.nan

def api_pg_dataset_linechart(url_dataset, url_reference_elements, log10=True):
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