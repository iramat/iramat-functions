def create_bulkupload(output_path="aeamena_data.xlsx", root_url = 'https://aema.huma-num.fr/back/public/api/', vocabs = [
        "ateliers", "objettypes", "collections", "communes", "contexte", "denominations",
        "mesuretypes", "emetteurs", "fonctions", "depots", "matieres", "observations",
        "pays", "periodes", "series", "objetsoustypes", "techniques", "tresors",
        "types", "descriptiftypes", "localisationtypes", "zones"
    ]
):
    """Fetches AeMA vocabs data, writes them to Excel sheets, and adds dropdowns in a summary sheet."""
    # TODO: transpose rows and columns in the Summary sheet

    import pandas as pd
    import requests
    from openpyxl import load_workbook
    from openpyxl.worksheet.datavalidation import DataValidation    

    # === 2. Fetch data ===
    dfs = []
    for vocab in vocabs:
        url = f"{root_url}{vocab}"
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            for item in data:
                item.pop('id', None)
            dfs.append(pd.DataFrame(data))
        except Exception as e:
            print(f"Error fetching {vocab}: {e}")
            dfs.append(pd.DataFrame())

    # === 3. Create summary sheet ===
    summary_rows = [
        {"sheet": sheet_name, "column": col}
        for sheet_name, df in zip(vocabs, dfs)
        for col in df.columns
    ]
    summary_df = pd.DataFrame(summary_rows)

    # === 4. Write to Excel ===
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        summary_df.to_excel(writer, sheet_name='Summary', index=False)
        for name, df in zip(vocabs, dfs):
            df.to_excel(writer, sheet_name=name, index=False)

    # === 5. Add dropdowns ===
    wb = load_workbook(output_path)
    summary_ws = wb["Summary"]
    dropdown_col_idx = 3
    summary_ws.cell(row=1, column=dropdown_col_idx, value="Dropdown")

    for i, row in enumerate(summary_ws.iter_rows(min_row=2, max_row=summary_ws.max_row, max_col=2), start=2):
        sheet_name, column_name = row[0].value, row[1].value
        if sheet_name in wb.sheetnames:
            sheet = wb[sheet_name]
            header = [cell.value for cell in sheet[1]]
            if column_name in header:
                col_idx = header.index(column_name) + 1
                col_data = list(sheet.iter_cols(min_col=col_idx, max_col=col_idx, min_row=2, values_only=True))[0]
                values = list(dict.fromkeys([str(v) for v in col_data if v]))

                # Build a dropdown list without exceeding Excel's formula limit
                joined = ""
                for value in values:
                    if len(joined) + len(value) + 1 <= 254:
                        joined += ("," if joined else "") + value
                    else:
                        break

                if joined:
                    dropdown_formula = f'"{joined}"'
                    dv = DataValidation(type="list", formula1=dropdown_formula, showDropDown=False)
                    summary_ws.add_data_validation(dv)
                    dv.add(summary_ws.cell(row=i, column=dropdown_col_idx))

    # === 6. Move Summary to first sheet and save ===
    wb._sheets.insert(0, wb._sheets.pop(wb.sheetnames.index("Summary")))
    wb.save(output_path)
    return(wb)
    # print(f"Excel file saved to: {output_path}")

def gallica_api(api_root = 'https://gallica.bnf.fr/services/OAIRecord?ark=', ark_id= 'btv1b104536783', verbose = True):
    """
    Collect Gallica data from different APIs

    :param api_root: API root path
    :param ark_id: Ark
    """
    import requests
    import xml.etree.ElementTree as ET
    import json

    GALLICA_URL = api_root + ark_id

    if api_root == 'https://gallica.bnf.fr/services/OAIRecord?ark=':
      if(verbose):
         print("collect parametric data")
      resp = requests.get(GALLICA_URL)
      if resp.status_code == 200:
          xml_data = resp.text
          root = ET.fromstring(xml_data)
          data = {
              "identifier": root.find(".//identifier").text if root.find(".//identifier") is not None else None,
              "title": root.find(".//dc:title", namespaces={"dc": "http://purl.org/dc/elements/1.1/"}).text if root.find(".//dc:title", namespaces={"dc": "http://purl.org/dc/elements/1.1/"}) is not None else None,
              "format": [fmt.text for fmt in root.findall(".//dc:format", namespaces={"dc": "http://purl.org/dc/elements/1.1/"})],
              "language": root.find(".//dc:language", namespaces={"dc": "http://purl.org/dc/elements/1.1/"}).text if root.find(".//dc:language", namespaces={"dc": "http://purl.org/dc/elements/1.1/"}) is not None else None,
              "relation": root.find(".//dc:relation", namespaces={"dc": "http://purl.org/dc/elements/1.1/"}).text if root.find(".//dc:relation", namespaces={"dc": "http://purl.org/dc/elements/1.1/"}) is not None else None,
              "types": [t.text for t in root.findall(".//dc:type", namespaces={"dc": "http://purl.org/dc/elements/1.1/"})],
              "source": root.find(".//dc:source", namespaces={"dc": "http://purl.org/dc/elements/1.1/"}).text if root.find(".//dc:source", namespaces={"dc": "http://purl.org/dc/elements/1.1/"}) is not None else None,
              "rights": [r.text for r in root.findall(".//dc:rights", namespaces={"dc": "http://purl.org/dc/elements/1.1/"})],
              "description": root.find(".//dc:description", namespaces={"dc": "http://purl.org/dc/elements/1.1/"}).text if root.find(".//dc:description", namespaces={"dc": "http://purl.org/dc/elements/1.1/"}) is not None else None,
          }
          json_output = json.dumps(data, indent=4, ensure_ascii=False).encode('utf8')
          return(json_output.decode())
      else:
          print(f"Error {resp.status_code}: Unable to fetch data from Gallica API")

    if api_root == 'https://gallica.bnf.fr/ark:/12148/':
      if(verbose):
         print("collect image thumbnail")
      GALLICA_URL = GALLICA_URL + '/thumbnail'
      resp = requests.get(GALLICA_URL)
      if resp.status_code == 200:
         return(resp.content)
      else:
          print(f"Failed to load image. HTTP Status Code: {resp.status_code}")

