from django.conf.urls.defaults import *
from django.conf import settings
from django.views.generic.simple import redirect_to

from humfrey.desc import views as desc_views
from humfrey.images import views as images_views
from opencitationsnet.core import views as core_views

#from humfrey.dataox.views import DatasetView, ExploreView, ExampleDetailView, ExampleResourceView, ExampleQueryView, ContactView, ForbiddenView, HelpView, ResizedImageView

urlpatterns = patterns('',
    (r'^$', core_views.IndexView(), {}, 'index'),
    (r'^id/.*$', desc_views.IdView(), {}, 'id'),

    (r'^doc.+$', desc_views.DocView(), {}, 'doc'),
    (r'^doc/$', desc_views.DocView(), {}, 'doc-generic'),
    (r'^desc/$', desc_views.DescView(), {}, 'desc'),

    (r'^search/$', core_views.SearchView(), {}, 'search'),
    (r'^citation-network/$', core_views.CitationNetworkView(), {}, 'citation-network'),

    (r'^journals/$', core_views.JournalListView(), {}, 'journal-list'),
    (r'^articles/$', core_views.ArticleListView(), {}, 'article-list'),
    (r'^organizations/$', core_views.OrganizationListView(), {}, 'organization-list'),

    (r'^sparql/$', desc_views.SparqlView(), {}, 'sparql'),

    (r'^forbidden/$', core_views.ForbiddenView(), {}, 'forbidden'),

    (r'^pingback/', include('humfrey.pingback.urls')),

    (r'^external-image/$', images_views.ResizedImageView(), {}, 'resized-image'),
)

handler500 = core_views.ServerErrorView()

if settings.DEBUG:
    urlpatterns += patterns('',
        url(r'^site-media/(?P<path>.*)$', 'django.views.static.serve', {
            'document_root': settings.MEDIA_ROOT,
        }),
   )

