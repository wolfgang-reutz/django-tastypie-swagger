try:
	from django.conf.urls import include, url
except ImportError:
	from django.conf.urls.defaults import include, url

from .views import SwaggerView, ResourcesView

urlpatterns = [
    url(r'^$', SwaggerView.as_view(), name='index'),
    url(r'^resources/$', ResourcesView.as_view(), name='resources'),
]
