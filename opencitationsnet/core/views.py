import datetime
import subprocess

import feedparser
import pytz
import rdflib
from rdflib import URIRef, Literal

from django.http import Http404, HttpResponse, HttpResponsePermanentRedirect
from django.core.urlresolvers import reverse
from django.conf import settings
from django.shortcuts import render_to_response
from django.template import loader, RequestContext
from django.template.defaultfilters import slugify


from humfrey.linkeddata.views import EndpointView, RDFView, ResultSetView
from humfrey.utils.resource import Resource
from humfrey.utils.namespaces import NS
from humfrey.utils.views import BaseView, renderer
from humfrey.utils.cache import cached_view

class IndexView(BaseView):
    def initial_context(self, request):
        try:
            feed = feedparser.parse("http://opencitations.wordpress.com/feed/")
            for entry in feed.entries:
                entry.updated_datetime = datetime.datetime(*entry.updated_parsed[:6], tzinfo=pytz.utc).astimezone(pytz.timezone(settings.TIME_ZONE))
        except Exception, e:
            raise
            feed = None
        return {
            'feed': feed,
        }

    @cached_view
    def handle_GET(self, request, context):
        return self.render(request, context, 'index')

class ForbiddenView(BaseView):
    @cached_view
    def handle_GET(self, request, context):
        context['status_code'] = 403
        return self.render(request, context, 'forbidden')

class NotFoundView(BaseView):
    def __init__(self, template_name):
        super(NotFoundView, self).__init__()
        self._template_name = template_name

    @cached_view
    def handle_GET(self, request, context):
        context['status_code'] = 404
        return self.render(request, context, self._template_name)

class ServerErrorView(BaseView):
    @cached_view
    def handle_GET(self, request, context):
        context['status_code'] = 500
        return self.render(request, context, '500')

class CannedQueryView(EndpointView, ResultSetView, RDFView):
    subject_type = None
    
    def handle_GET(self, request, context):
        results = self.endpoint.query(self._QUERY)

        if isinstance(results, list):
            context['results'] = results
        elif isinstance(results, rdflib.ConjunctiveGraph):
            context['graph'] = results
            context['subjects'] = set(Resource(s, results, self.endpoint) for s in results.subjects(NS.rdf.type, self.subject_type))
        elif isinstance(results, bool):
            context['result'] = results
        if hasattr(results, 'query'):
            context['queries'] = [results.query]

        return self.render(request, context, self.template_name)      

class SearchView(EndpointView, ResultSetView):
    _QUERY = """
      SELECT ?thing (SAMPLE(?label_) as ?label) (SAMPLE(?type_) as ?type) WHERE {
        ?thing ?p %s ;
          a ?type_ .
        FILTER (?p in (prism:issn, prism:eIssn, prism:isbn, prism:doi, fabio:hasPubMedId, fabio:hasPubMedCentralId, dcterms:identifier, rdfs:label, skos:prefLabel, dcterms:title, foaf:name)) .
        OPTIONAL {
          ?thing ?label_predicate ?label_ .
          FILTER (?label_predicate in (skos:prefLabel, rdfs:label, dcterms:title, foaf:name, dcterms:identifier, rdfs:label))
        } .
      } GROUP BY ?thing LIMIT 100
    """

    def handle_GET(self, request, context):
        query_term = (request.GET.get('identifier') or request.GET.get('query', '')).strip()
        if query_term:
            self.perform_query(request, context, query_term)
        return self.render(request, context, 'search')

    def perform_query(self, request, context, query_term):
        results = self.endpoint.query(self._QUERY % Literal(query_term).n3())
        context.update({
            'results': results,
            'queries': [results.query],
            'query': request.GET.get('query', ''),
            'identifier': request.GET.get('identifier', ''),
        })

class JournalListView(CannedQueryView):
    _QUERY = """
      SELECT ?journal ?title ?issn ?eissn WHERE {
        ?journal prism:issn ?issn ;
          a fabio:Journal ;
          dcterms:title ?title .
        OPTIONAL { ?journal prism:eIssn ?eissn }
      } ORDER BY ?title
    """

    template_name = 'journal_list'

class ArticleListView(CannedQueryView):
    _QUERY = """
      CONSTRUCT {
        ?article a fabio:JournalArticle ;
          dcterms:title ?title ;
          dcterms:creator ?creator ;
          dcterms:date ?date ;
          prism:doi ?doi ;
          fabio:hasPubMedId ?pmid ;
          fabio:hasPubMedCentralId ?pmc .
        ?creator a foaf:Person ;
          foaf:name ?creator_name .
       } WHERE {
         { SELECT * WHERE { ?article a fabio:JournalArticle ; dcterms:title ?title } LIMIT 200 } .
         OPTIONAL { ?article dcterms:creator ?creator . ?creator a foaf:Person ; foaf:name ?creator_name } .
         OPTIONAL { ?article prism:doi ?doi } .
         OPTIONAL { ?article fabio:hasPubMedId ?pmid } .
         OPTIONAL { ?article fabio:hasPubMedCentralId ?pmc } .
         OPTIONAL { ?article dcterms:date ?date } .
      } LIMIT 200
    """

    subject_type = NS.fabio.JournalArticle
    template_name = 'article_list'

class OrganizationListView(CannedQueryView):
    _QUERY = """
      SELECT ?organization (SAMPLE(?name_) as ?name) (SAMPLE(?address_) as ?address) WHERE {
        ?organization a org:Organization ;
          rdfs:label ?name_ .
        OPTIONAL { ?organization v:adr/rdfs:label ?address_ } .
      } GROUP BY ?organization LIMIT 200
    """

    template_name = 'organization_list'

class CitationNetworkView(EndpointView, RDFView):
    _DIRECTIONS = {
        'citedBy': 'cito:cites{,%(depth)d}',
        'cites': '^cito:cites{,%(depth)d}',
        'all': '(cito:cites|^cito:cites){,%(depth)d}',
        'both': 'cito:cites{,%(depth)d}|(^cito:cites){,%(depth)d}',
    }

    _QUERY = """
      CONSTRUCT {
        ?article a ?type ;
          dcterms:title ?title ;
          dcterms:published ?published ;
          cito:cites ?cited .
        ?cited a ?citedType ;
          dcterms:title ?citedTitle ;
          dcterms:published ?citedPublished .
      } WHERE {
        { SELECT DISTINCT ?article WHERE { ?article %(direction)s %(uri)s } } .
        ?article a ?type ;
          dcterms:title ?title .
        OPTIONAL { ?article dcterms:published ?published } .
        OPTIONAL {
          ?article cito:cites ?cited .
        } .
      }
    """
    def handle_GET(self, request, context):
        uri = URIRef(request.GET.get('uri', ''))
        types = self.get_types(uri)
        if not types:
            raise Http404
        try:
            depth = max(0, min(int(request.GET.get('depth')), 3))
        except (TypeError, ValueError):
            depth = 2 

        try:
            direction = self._DIRECTIONS[request.GET['direction']]
        except KeyError:
            direction = self._DIRECTIONS['both']
        direction = direction  % {'depth': depth}

        query = self._QUERY % {'uri': uri.n3(), 'direction': direction}
        graph = self.endpoint.query(query)

        subjects = [Resource(s, graph, self.endpoint) for s in set(graph.subjects(NS.rdf.type))]
        hexhashes = set(s.hexhash for s in subjects)

        context.update({
            'graph': graph,
            'queries': [graph.query],
            'subjects': subjects,
            'subject': Resource(uri, graph, self.endpoint),
            'hexhashes': hexhashes,
            'depth': depth,
            'layout': request.GET.get('layout'),
            'direction': request.GET.get('direction'),
            'minimal': request.GET.get('minimal'),
            
        })

        return self.render(request, context, 'citation-network')

    _DOT_LAYOUTS = "circo dot fdp neato nop nop1 nop2 osage patchwork sfdp twopi".split()
    _DOT_OUTPUTS = [
        dict(format='bmp', mimetypes=('image/x-bmp','image/x-ms-bmp'), name='BMP', dot_output='bmp'),
        dict(format='xdot', mimetypes=('text/vnd.graphviz',), name='xDOT', dot_output='xdot', priority=0.9),
        dict(format='gv', mimetypes=('text/vnd.graphviz',), name='DOT (GraphViz)', dot_output='gv'),
        dict(format='jpeg', mimetypes=('image/jpeg',), name='JPEG', dot_output='jpeg'),
        dict(format='png', mimetypes=('image/png',), name='PNG', dot_output='png'),
        dict(format='ps', mimetypes=('application/postscript',), name='PostScript', dot_output='ps'),
        dict(format='pdf', mimetypes=('application/pdf',), name='PDF', dot_output='pdf'),
        dict(format='svg', mimetypes=('image/svg+xml',), name='SVG', dot_output='svg'),
    ]

    def _get_dot_renderer(output):
        def dot_renderer(self, request, context, template_name):
            layout = request.GET.get('layout')
            if layout not in self._DOT_LAYOUTS:
                layout = 'fdp'
            template = loader.get_template(template_name + '.gv')
            plain_gv = template.render(RequestContext(request, context))
            dot = subprocess.Popen(['dot', '-K'+layout, '-T'+dot_output], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
            dot_stdout, _ = dot.communicate(input=plain_gv.encode('utf-8'))
            response = HttpResponse(dot_stdout, mimetype=output['mimetypes'][0])
            response['Content-Disposition'] = 'inline; filename="%s.%s"' % (slugify(context['subject'].dcterms_title)[:32], output['format'])
            return response

        dot_output = output.pop('dot_output')
        dot_renderer.__name__ = 'render_%s' % output['format']
        return renderer(**output)(dot_renderer)

    for output in _DOT_OUTPUTS:
        locals()['render_%s' % output['format']] = _get_dot_renderer(output)
    del _get_dot_renderer, output


    @renderer(format="gv", mimetypes=('text/vnd.graphviz',), name="DOT (GraphViz)")
    def render_gv(self, request, context, template_name):
        layout = request.GET.get('layout')
        if layout not in self._DOT_LAYOUTS:
            layout = 'fdp'
        template = loader.get_template(template_name + '.gv')
        plain_gv = template.render(RequestContext(request, context))
        dot = subprocess.Popen(['dot', '-K'+layout, '-Txdot'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        dot_stdout, _ = dot.communicate(input=plain_gv.encode('utf-8'))
        response = HttpResponse(dot_stdout, mimetype='text/vnd.graphviz')
        response['Content-Disposition'] = 'attachment; filename="%s.gv"' % slugify(context['subject'].dcterms_title)[:32]
        return response

    @renderer(format="graphml", mimetypes=('application/x-graphml+xml',), name="GraphML")
    def render_graphml(self, request, context, template_name):
        response = render_to_response(template_name + '.graphml',
                                      context, context_instance=RequestContext(request),
                                      mimetype='application/x-graphml+xml')
        response['Content-Disposition'] = 'attachment; filename="%s.graphml"' % slugify(context['subject'].dcterms_title)[:32]
        return response
