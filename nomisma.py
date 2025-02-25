def resume_concept_if(g = 'C:/Rprojects/iramat-test/credentials/pg_credentials.json', verbose = True):
    """
    Parse a RDF triple and extract relevant information

    :param g: a RDF graph created by rdflib.Graph()
    """
    import rdflib

    predicates_of_interest = {
        "prefLabel": rdflib.URIRef("http://www.w3.org/2004/02/skos/core#prefLabel"),
        "definition": rdflib.term.URIRef('http://www.w3.org/2004/02/skos/core#definition'),
        "topic": rdflib.URIRef("http://xmlns.com/foaf/0.1/topic"),
    }

    # Extract relevant data
    extracted_data = {key: [] for key in predicates_of_interest}

    for s, p, o in g:
        for key, target_pred in predicates_of_interest.items():
            if p == target_pred:
                if isinstance(o, rdflib.Literal):
                    extracted_data[key].append(f"{o.value} (lang='{o.language}')" if o.language else o.value)
                else:
                    extracted_data[key].append(o)
    return(extracted_data)