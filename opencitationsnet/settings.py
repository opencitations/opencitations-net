from __future__ import absolute_import
import os

from humfrey.settings.common import *

ADMINS = (
    ('Alexander Dutton', 'alexander.dutton@zoo.ox.ac.uk'),
)

MANAGERS = ADMINS

INSTALLED_APPS += (
    'opencitationsnet.core',
    'django_hosts',
)

MEDIA_URL = '//opencitations.net/site-media/'

MIDDLEWARE_CLASSES = ('django_hosts.middleware.HostsMiddleware',) + MIDDLEWARE_CLASSES

ROOT_URLCONF = 'opencitationsnet.urls.empty'
ROOT_HOSTCONF = 'opencitationsnet.hosts'
DEFAULT_HOST = 'data'
MEDIA_ROOT = os.path.join(os.path.dirname(__file__), 'media')

ADDITIONAL_NAMESPACES = {
    'frbr': 'http://purl.org/vocab/frbr/core#',

    # SPAR
    'biro': 'http://purl.org/spar/biro/',
    'c4o': 'http://purl.org/spar/c4o/',
    'cito': 'http://purl.org/spar/cito/',
    'pro': 'http://purl.org/spar/pro/',
    'pso': 'http://purl.org/spar/pso/',

    'collections': 'http://swan.mindinformatics.org/ontologies/1.2/collections/',
    'dcterms': 'http://purl.org/dc/terms/',
    'fabio': 'http://purl.org/spar/fabio/',
    'foaf': 'http://xmlns.com/foaf/0.1/',
    'org': 'http://www.w3.org/ns/org#',
    'ov': 'http://open.vocab.org/terms/',
    'prism': 'http://prismstandard.org/namespaces/basic/2.0/',
    'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
    'rdfs': 'http://www.w3.org/2000/01/rdf-schema#',
    'skos': 'http://www.w3.org/2004/02/skos/core#',
    'v': 'http://www.w3.org/2006/vcard/ns#',
    'xsd': 'http://www.w3.org/2001/XMLSchema#',
}


TEMPLATE_DIRS = (
    os.path.join(os.path.dirname(__file__), 'templates'),
) + TEMPLATE_DIRS

ID_MAPPING = (
    ('http://opencitations.net/id/', 'http://opencitations.net/doc/', True),
)

SERVED_DOMAINS = (
    'opencitations.net',
)

DOC_RDF_PROCESSORS += (
    'opencitationsnet.core.rdf_processors.license_statement',
)

