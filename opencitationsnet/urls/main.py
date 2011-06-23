from django.conf.urls.defaults import *
from django.conf import settings
from django.views.generic.simple import redirect_to

from humfrey.desc.views import IdView, DocView, DescView, SparqlView
from humfrey.images.views import ResizedImageView
from opencitationsnet.core.views import IndexView

from opencitationsnet.core.views import ServerErrorView, ForbiddenView

#from humfrey.dataox.views import DatasetView, ExploreView, ExampleDetailView, ExampleResourceView, ExampleQueryView, ContactView, ForbiddenView, HelpView, ResizedImageView

urlpatterns = patterns('',
    (r'^$', IndexView(), {}, 'index'),
    (r'^id/.*$', IdView(), {}, 'id'),

    (r'^doc.+$', DocView(), {}, 'doc'),
    (r'^doc/$', DocView(), {}, 'doc-generic'),
    (r'^desc/$', DescView(), {}, 'desc'),

    (r'^sparql/$', SparqlView(), {}, 'sparql'),

    (r'^forbidden/$', ForbiddenView(), {}, 'forbidden'),

    (r'^pingback/', include('humfrey.pingback.urls')),

    (r'^external-image/$', ResizedImageView(), {}, 'resized-image'),    
)

handler500 = ServerErrorView()

if settings.DEBUG:
    urlpatterns += patterns('',
        url(r'^site-media/(?P<path>.*)$', 'django.views.static.serve', {
            'document_root': settings.MEDIA_ROOT,
        }),
   )

