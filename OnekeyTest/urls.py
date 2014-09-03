from django.conf.urls import patterns, include, url

from django.contrib import admin
import settings
import autotest.views
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'OnekeyTest.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),
	(r'^site_media/(?P<path>.*)$','django.views.static.serve',{'document_root':settings.STATIC_URL}), 
    url(r'^admin/', include(admin.site.urls)),
	url(r'^$', autotest.views.main),
)
