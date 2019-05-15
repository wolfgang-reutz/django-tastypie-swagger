Synopsis
========

**django-tastypie-swagger** is a small adapter library to construct Swagger_ documentation from Tastypie_ resources.

This package provides two things:

1. An embedded instance of `Swagger UI`_ to point a URL to.
2. Automatic `Resource Listing`_ and `API Declaration`_ generation that is consumed by #1

Installing for Production
=========================

.. code-block::

   pip install django-tastypie-swagger-ng

Installing for Development
==========================

.. code-block::

   git clone https://github.com/ifanrx/django-tastypie-swagger.git
   pip install -e django-tastypie-swagger

Usage
=====

Add to INSTALLED_APPS::

    INSTALLED_APPS = [
        ...

        'tastypie_swagger',

        ...
    ]

Define **TASTYPIE_SWAGGER_API_MODULE_LIST** in your settings::

    TASTYPIE_SWAGGER_API_MODULE_LIST = (
        {'path': 'app_name.path',
         'obj': 'xxx',
         'func_name': 'xxx'},

        {'path': 'app_name.path',
         'obj': 'xxx',
         'func_name': 'xxx'}
    )

Optionally define **TASTYPIE_SWAGGER_INFO** in your settings, see https://swagger.io/specification/#infoObject for details:

    TASTYPIE_SWAGGER_INFO = {
        'version': '1.0.0',
        'title': 'My awesome API',
        'description': 'describe what it does',
    }

**TASTYPIE_SWAGGER_API_MODULE_LIST** is an iterable object.
Each item is a dict.

- path: It should be a python path can find your api instance, like polls.api(polls is your APP's name, there is a api.py in directory polls)
- obj: It should be an Api instance or an instance who have a function to get an Api instance
- func_name: if isinstance(obj, Api) is True, func_name should be ''

Include in your urlconf with namespace **tastypie_swagger**::

    urlpatterns = patterns('',
        ...

        url(r'api/doc/', include('tastypie_swagger.urls', namespace='tastypie_swagger')),

        ...
    )


Swagger documentation will be served up at the URL you configured.

Using ``extra_actions``
--------------------

While most **ModelResource** based endpoints are good *as-is* there are times
when adding additional functionality (`like search <http://django-tastypie.readthedocs.org/en/latest/cookbook.html#adding-search-functionality>`_)
is required. In Tastypie the recommended way do to this is by overriding the
``prepend_urls`` function and returning a list of urls that describe additional
endpoints. How do you make the schema map represent these endpoints so they are
properly documented?::

Add an attribute to the ``Meta`` class inside your **ModelResource** class
called ``extra_actions``. Following the Tastypie search example, here is how
``extra_actions`` should be defined::

    class Meta:
        ...
        extra_actions = [
            {
                "name": "search",
                "http_method": "GET",
                "resource_type": "list",
                "description": "Seach endpoint",
                "fields": {
                    "q": {
                        "type": "string",
                        "required": True,
                        "description": "Search query terms"
                    }
                }
            }
        ]

``extra_actions`` is a list of dictionary objects that define extra endpoints
that are unavailable to introspection.

.. important::
   ``extra_actions`` feeds directly into the schema **for swagger**. It does
   not alter the tastypie schema listing tastypie provides.

Top level keys and meaning in the ``extra_actions`` dictionary:

- ``name``: **Required**. Nickname of the resource.
- ``http_method``: Defaults to ``"GET"``. HTTP method allowed here as a string.
  Will be uppercased on output.
- ``resource_type``: If this is declared as ``"list"`` then the endpoint
  **will not** include a ``{id}`` parameter in the uri or in the parameters
  list. This is applicable to endpoints such as the above example that filter
  or perform actions across many items. If ``resource_type`` is ommitted and
  the ``http_method`` is ``"GET"`` then the endpoint will default to ``"view"``
  and include a ``{id}`` parameter in the uri and parameter list.
- ``description``: Description of this endpoint.
- ``fields``: Dictionary of parameters this endpoint accepts.

Field dictionaries are declared in a ``{ "name": { [options dict] }`` style.
This is done for compatability reasons with older versions of
django-tastypie-swagger.

.. warning::
   The structure of ``fields`` will likely change in future versions if
   `Joshua Kehn`_ continues committing.

Available keys and meaning for the ``fields`` dictionary.::

 - ``type``: Defaults to ``"string"``. Parameter type.
 - ``required``: Defaults to ``False``.
 - ``description``: Defaults to ``""`` (empty string). Description of this
   parameter.


Detecting required fields
-------------------------

Tastypie 0.9.11 **ModelResource** fields do not respect the *blank* attribute on django model fields, which this library depends on to determine if a field is required or not.

You can use `this ModelResource subclass <https://gist.github.com/4041352>`_ as a workaround to this issue.


Swagger-UI Version
==================

https://github.com/swagger-api/swagger-ui/tree/v3.17.0

OpenAPI-Specification
=====================

https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.1.md



.. _Swagger: http://swagger.wordnik.com/
.. _Tastypie: https://django-tastypie.readthedocs.org
.. _Resource Listing: https://github.com/wordnik/swagger-core/wiki/Resource-Listing
.. _API Declaration: https://github.com/wordnik/swagger-core/wiki/API-Declaration
.. _Swagger UI: https://github.com/wordnik/swagger-ui
.. _tastypie.api.Api: https://django-tastypie.readthedocs.org/en/latest/api.html
.. _Joshua Kehn: mailto:josh@kehn.us
