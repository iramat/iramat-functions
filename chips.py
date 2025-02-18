def db_connect(pg_creds = 'C:/Rprojects/iramat-test/credentials/pg_credentials.json', verbose = True):
	"""
	Connect a database

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
