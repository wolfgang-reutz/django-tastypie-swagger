import sys
import json

from django.views.generic import TemplateView
from django.http import HttpResponse, Http404
from django.core.exceptions import ImproperlyConfigured
from django.core.urlresolvers import reverse
from django.conf import settings

from tastypie.api import Api

from .mapping import ResourceSwaggerMapping


class TastypieApiMixin(object):
    """
    Provides views with a 'tastypie_api' attr representing a tastypie.api.Api instance

    Python path must be defined in settings as TASTYPIE_SWAGGER_API_MODULE
    """
    def __init__(self, *args, **kwargs):
        super(TastypieApiMixin, self).__init__(*args, **kwargs)
        self.tastypie_api_list = []
        tastypie_api_module_list = getattr(settings, 'TASTYPIE_SWAGGER_API_MODULE_LIST', None)
        if not tastypie_api_module_list:
            raise ImproperlyConfigured("Must define TASTYPIE_SWAGGER_API_MODULE in settings as path to a tastypie.api.Api instance")
        for tastypie_api_module in tastypie_api_module_list:
            path = tastypie_api_module['path']
            obj = tastypie_api_module['obj']
            func_name = tastypie_api_module['func_name']
            try:
                tastypie_api = getattr(sys.modules[path], obj, None)
                if func_name:
                    tastypie_api = getattr(tastypie_api, func_name)()
            except KeyError:
                raise ImproperlyConfigured("%s is not a valid python path" % path)
            if not isinstance(tastypie_api, Api):
                raise ImproperlyConfigured("%s is not a valid tastypie.api.Api instance" % tastypie_api_module)
            self.tastypie_api_list.append(tastypie_api)


class SwaggerApiDataMixin(object):
    """
    Provides required API context data
    """

    def get_context_data(self, *args, **kwargs):
        context = super(SwaggerApiDataMixin, self).get_context_data(*args, **kwargs)
        context.update({
            # TODO: How should versions be controlled?
            'apiVersion': '0.1',
            'swaggerVersion': '1.1',
        })
        return context


class JSONView(TemplateView):
    """
    Simple JSON rendering
    """
    response_class = HttpResponse

    def render_to_response(self, context, **response_kwargs):
        """
        Returns a response with a template rendered with the given context.
        """

        for k in ['params','view']:
            if k in context:
                del context[k]

        return self.response_class(
            json.dumps(context),
            content_type='application/json',
            **response_kwargs
        )


class SwaggerView(TastypieApiMixin, TemplateView):
    """
    Display the swagger-ui page
    """

    template_name = 'tastypie_swagger/index.html'


class ResourcesView(TastypieApiMixin, SwaggerApiDataMixin, JSONView):
    """
    Provide a top-level resource listing for swagger

    This JSON must conform to https://github.com/wordnik/swagger-core/wiki/Resource-Listing
    """

    def get_context_data(self, *args, **kwargs):
        context = super(ResourcesView, self).get_context_data(*args, **kwargs)

        # Construct schema endpoints from resources
        apis = []
        for tastypie_api in self.tastypie_api_list:
            for name in sorted(tastypie_api._registry):
                apis.append({'path': '/%s/%s' % (tastypie_api.api_name, name)})
        context.update({
            'basePath': self.request.build_absolute_uri(reverse('tastypie_swagger:schema')),
            'apis': apis,
        })
        return context


class SchemaView(TastypieApiMixin, SwaggerApiDataMixin, JSONView):
    """
    Provide an individual resource schema for swagger

    This JSON must conform to https://github.com/wordnik/swagger-core/wiki/API-Declaration
    """

    def get_context_data(self, *args, **kwargs):
        # Verify matching tastypie resource exists
        api_name = kwargs.get('api_name', None)
        resource_name = kwargs.get('resource', None)
        api_name_list = [api.api_name for api in self.tastypie_api_list]

        if not api_name in api_name_list:
            print api_name_list
            print 'no api name'
            raise Http404

        for api in self.tastypie_api_list:
            if api_name == api.api_name:
                tastypie_api = api
                break;

        if not resource_name in tastypie_api._registry:
            print tastypie_api._registry
            print 'no resource name'
            raise Http404

        # Generate mapping from tastypie.resources.Resource.build_schema
        resource = tastypie_api._registry.get(resource_name)
        mapping = ResourceSwaggerMapping(resource)

        context = super(SchemaView, self).get_context_data(*args, **kwargs)
        context.update({
            'basePath': '/',
            'apis': mapping.build_apis(),
            'models': mapping.build_models()
        })
        return context
