import rdflib

from humfrey.utils.namespaces import NS

def license_statement(graph, doc_uri, subject_uri, subject, endpoint, renderers):
    graph.add((doc_uri, NS['dcterms'].license, rdflib.URIRef('http://creativecommons.org/publicdomain/zero/1.0/')))
