import datetime

import feedparser, pytz

from django.http import Http404, HttpResponsePermanentRedirect
from django.core.urlresolvers import reverse
from django.conf import settings

from humfrey.linkeddata.views import EndpointView, RDFView, ResultSetView
from humfrey.utils.resource import Resource
from humfrey.utils.namespaces import NS
from humfrey.utils.views import BaseView
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
