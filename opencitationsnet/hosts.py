from django_hosts import patterns, host

host_patterns = patterns('',
    host(r'opencitations.net', 'opencitationsnet.urls.main', name='data'),
    host(r'$x^', 'opencitationsnet.urls.empty', name='empty'),
)
