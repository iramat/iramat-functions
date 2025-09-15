def db_connect(pg_creds = 'C:/Users/TH282424/Rprojects/iramat-test/credentials/pg_credentials.json', verbose = True):
  """
  Connect a database connection (engine)

  :param pg_creds: my PG credentials (local)
  
  >>> engine = db_connect("pg_credentials.json") 
  """
  from sqlalchemy import create_engine
  import json

  # read credentials (secret) and connect the Pg DB
  if verbose:
      print("Read Pg")
  with open(pg_creds, 'r') as file:
      db_config = json.load(file)
  connection_str = f"postgresql://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['dbname']}"
  engine = create_engine(connection_str)

  return(engine)

def db_query(query = "SELECT * FROM instrument_incertitude;", engine=None, verbose = True):
  """
  Query a database

  :param query: a SQL query, default: View 'instrument_incertitude'
  :param engine: a sqlalchemy.engine
  """
  import pandas as pd

  df = pd.read_sql(query, engine)
  return(df)

def db_store(data=None, verbose = True):
  """
  Store a dataset in a local temp file 

  :param data: a dataset
  """
  import tempfile

  tmp = tempfile.NamedTemporaryFile()
  with open(tmp.name, 'w') as f:
      f.write(data)
  
  return(tmp.name)


def db_refbib(table = "instrument_incertitude", engine=None, output_format = "JSON", verbose = True):
  """
  Query a table of bibliographic references related to different views. This bibliographic reference is for the whole Postgres table or view. It is different from bibliographic references related to rows. Bibliographic references are stored in the table '_refbib'. These references are stored as text, in a bibtex layout, in the column 'ref_biblio'. 

  :param table: the selected table or view
  :param engine: a sqlalchemy.engine
  :param output_format: the output format (default: JSON).

  >>> # JSON format (JSON object)
  >>> bibref_json = ch.db_refbib(table = "instrument_incertitude", engine=engine, output_format = "JSON")
  >>> print(f"📚 Bibliographic Reference in JSON format:\n{bibref_json}")

  >>> # IEEE format
  >>> bibref_ieee = ch.db_refbib(table = "instrument_incertitude", engine=engine, output_format = "IEEE")
  >>> print(f"📚 Bibliographic Reference in IEEE style:\n{bibref_ieee}")
  """
  import json
  import psycopg2
  import bibtexparser
  from bibtexparser.customization import convert_to_unicode
  from pybtex.database import parse_string
  from pybtex.plugin import find_plugin

  db_params = json.load(open("pg_credentials.json"))

  conn = psycopg2.connect(**db_params)
  cur = conn.cursor()
  cur.execute(f"SELECT ref_biblio FROM _refbib WHERE ref_table='{table}'")
  row = cur.fetchone()
  # Close connection
  cur.close()
  conn.close()

  try:
    bibtex_entry = row[0]  # Extract the BibTeX string
  except:
      print("Pas d'entrée bibliographique pour cette vue")

  if(output_format == "JSON"):
    #TODO: check bibtex syntax
    bib_data = bibtexparser.loads(bibtex_entry)
    output = json.dumps(bib_data.entries, indent=4, ensure_ascii=False)
    bibref = json.loads(output)
    return(bibref)
  if(output_format == "IEEE"):
    bib_data = parse_string(bibtex_entry, "bibtex")
    # Find the style formatter
    ieee_style = find_plugin("pybtex.style.formatting", "unsrt")()  # "unsrt" is closest to IEEE
    formatted_entries = ieee_style.format_entries(bib_data.entries.values())
    # return the entries as a list instead of a generator
    ieee = list(formatted_entries)
    first_bib = ieee[0]
    bibref = first_bib.text.render_as("text")
    return(bibref)
    # return(list(formatted_entries))

def db_edtf_maj(engine = None):
  """
  Update the edtf field from 'date_debut', 'date_fin', and 'doute_date' fields from the 'sites' table

  :param engine: a sqlalchemy.engine
  """
  from sqlalchemy import create_engine, text
  
  with engine.begin() as conn:  # begin() ensures commit
    conn.execute(text("""
        ALTER TABLE sites
        ADD COLUMN IF NOT EXISTS edtf text;
    """))
    result = conn.execute(text("""
        SELECT id_site, date_debut, date_fin, doute_date FROM sites;
    """))
    rows = result.fetchall()

    # update each row
    for site_id, date_debut, date_fin, doute_date in rows:
        edtf_val = db_edtf_build_edtf(date_debut, date_fin, doute_date)
        conn.execute(
            text("UPDATE sites SET edtf = :edtf WHERE id_site = :id"),
            {"edtf": edtf_val, "id": site_id}
        )

# import psycopg2
# import pandas as pd

def db_edtf_format_year(year: int | None) -> str | None:
    """Format integer year to EDTF padded string, or None if missing."""
    if year is None:
        return None
    if year < 0:
        return f"{year:05d}"   # e.g. -25 -> -0025
    else:
        return f"{year:04d}"   # e.g. 450 -> 0450

def db_edtf_build_edtf(start: int | None, end: int | None, doute: bool | None) -> str | None:
    """Construct EDTF interval string with ~ and optional ?."""
    if start is None or end is None:
        return None
    start_str = db_edtf_format_year(start)
    end_str = db_edtf_format_year(end)
    suffix = "~" if doute is False else "?~"
    return f"{start_str}{suffix}/{end_str}{suffix}"

def py_tempfile(response=None, module_name = "bdd"):
  """
  Save a content (typically a GitHub hosted file) in a temp folder

  :param response: a kind of requests.get(GitHub url)
  :param module_name: the name to give to the module, default 'bdd'
  """
  import tempfile
  import importlib.util

  with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as tmp_file:
    tmp_file.write(response.content)
    tmp_file_path = tmp_file.name

  # Import the module
  spec = importlib.util.spec_from_file_location(module_name, tmp_file_path)
  module = importlib.util.module_from_spec(spec)
  spec.loader.exec_module(module)

def zn_metadata(meta_data = None, verbose = True):
  """
  Fill a metadata template to be pushed on Zenodo from a bibtex reference stored in Postgres (table '_refbib'). This function is called after `db_refbib()`

  :param meta_data: a JSON object
  """

  #TODO: check values, map values (https://github.com/zoometh/iramat-test/blob/main/projects/citation/bibtex2zenodo.tsv)

  metadata = {
      'metadata': {
          'title': meta_data[0]['title'],
          'description': meta_data[0]['abstract'],
          'upload_type': 'dataset',
          'license': 'cc-by',
          'subjects': [{"term": "Archaeometry", "identifier": "http://id.loc.gov/authorities/subjects/sh85006517", "scheme": "url"},
                       {"term": "laboratory methods", "identifier": "https://apps.usgs.gov/thesaurus/term-simple.php?thcode=2&code=619", "scheme": "url"},
                       {"term": "chemical elements", "identifier": "https://apps.usgs.gov/thesaurus/term-simple.php?thcode=2&code=1427", "scheme": "url"}],
          'method': 'IRAMAT data entry methodology',
          'creators': [{'name': meta_data[0]['author'],
                        'affiliation': "IRAMAT"}],
          'keywords': meta_data[0]['keywords'],
          'dates': [{"start": meta_data[0]['year'], "end": meta_data[0]['year'], "type": "Collected", "description": "Lorem Ipsum dates"}],
      }
  }
  return(metadata)
