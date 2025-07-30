def read_data_urls(root_data_url="https://raw.githubusercontent.com/iramat/iramat-dev/refs/heads/main/dbs/chips/urls_data.tsv", reference="http://157.136.252.188:3000/ref_elements", read_ref=False):
    """
    Read a GitHub dataset (TSV file) and retrieve URLs, values and other infos

    >>> df = read_data_urls(read_ref=False)
    >>> print(df['url_data'])
    """
    import pandas as pd
    import re

    # response_data_ref_list = requests.get(root_data_url)
    # response_data_ref_list.content
    df = pd.read_csv(root_data_url, sep='\t')
    # convert to lower
    df['is_reference_data'] = df['is_reference_data'].str.lower()
    if(read_ref):
        # read ref only
        df = df.loc[df['is_reference_data'] == 'y']
    if(not read_ref):
        df = df.loc[df['is_reference_data'] != 'y']
    urls_data = list(df['url_data'])
    description = list(df['description'])
    dataset_names = [re.search(r'[^/]+$', url).group() for url in urls_data]
    return {
        "url_reference": reference,
        "url_data": urls_data,
        "dataset_name": dataset_names,
        "description": description # TODO: grab bib ref
    }



