def db_connect(pg_creds = 'C:/Rprojects/iramat-test/credentials/pg_credentials.json', verbose = True):
    """
    Connect a database connection (engine)

    :param pg_creds: my PG credentials (local)
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


def db_refbib(table = "instrument_incertitude", engine=None, output_format = "IEEE", verbose = True):
  """
  Query a table of bibliographic references related to different view. This is different from bibliographic refrences related to rows. Bibliographic references are stored in the table '_refbib'. These references are stored as text, with a bibtex format, in the column 'ref_biblio ' 

  :param table: the selected table or view
  :param engine: a sqlalchemy.engine
  :param output_format: the output format (default: IEEE)
  """
  import pandas as pd
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
    bib_data = bibtexparser.loads(bibtex_entry)
    output = json.dumps(bib_data.entries, indent=4, ensure_ascii=False)
    return(output)
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