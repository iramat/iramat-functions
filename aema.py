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

