# _*_ coding:utf-8 _*_
import sys
import json

from django.views.generic import TemplateView
from django.http import HttpResponse, Http404
from django.core.exceptions import ImproperlyConfigured
from django.core.urlresolvers import reverse
from django.conf import settings

from tastypie.api import Api

from .mapping import ResourceSwaggerMapping

from pprint import pformat

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
            'openapi': '3.0.1',
            'info': getattr(settings, 'TASTYPIE_SWAGGER_INFO', {
                'version': '1.0.0',
                "description": "ifanr 后端所有的 API",
                'title': 'ifanr API Center',
                'license': {
                    'name': 'Private'
                }
            }),
            'servers': [
                {
                   'url': self.request.build_absolute_uri('/')
                }
            ],
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

        for k in ['params', 'view']:
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

    def get_context_data(self, **kwargs):
        context = super(SwaggerView, self).get_context_data(**kwargs)
        context['supported_submit_methods'] = getattr(settings, 'TASTYPIE_SUPPORTED_SUBMIT_METHODS', [])
        return context


class ResourcesView(TastypieApiMixin, SwaggerApiDataMixin, JSONView):
    """
    Provide json data to swagger-ui page

    This JSON must conform to
    https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.1.md
    """

    def get_context_data(self, *args, **kwargs):
        context = super(ResourcesView, self).get_context_data(*args, **kwargs)

        # Construct schema endpoints from resources
        paths = {}
        tags = []
        for tastypie_api in self.tastypie_api_list:
            for name in sorted(tastypie_api._registry.keys()):
                mapping = ResourceSwaggerMapping(tastypie_api._registry.get(name))
                # 一个 resource 可能有多个 URL
                doc = mapping.resource.__doc__
                if doc:
                    try:
                        paths.update(json.loads(doc))
                    except ValueError:
                        paths.update(mapping.build_paths())
                else:
                    paths.update(mapping.build_paths())
                tag = mapping.build_global_tag()
                if (not any(x['name'] == tag['name'] for x in tags)):
                    tags.append(tag)
        context.update({
            'paths': paths,
        })
        if len(tags) > 0:
            context.update({'tags': tags})
        return context
