Skip the discovery
==================

Use this guide to describe the server with local files instead of querying it before each request.
Each command then sends three fewer requests.
The files also help with a server whose discovery endpoints are slow or incomplete.

Before sending a request, scim2-cli queries the discovery endpoints of the server:
``/Schemas``, ``/ResourceTypes`` and ``/ServiceProviderConfig``.
Each of the :option:`--schemas <scim2 --schemas>`, :option:`--resource-types <scim2 --resource-types>`
and :option:`--service-provider-config <scim2 --service-provider-config>` options replaces one of these requests with a JSON file.
The endpoints without a file are still queried.

Save the discovery resources
----------------------------

Query the three endpoints once, and keep the responses:

.. code-block:: console

    $ scim2 query schema > schemas.json
    $ scim2 query resourcetype > resource-types.json
    $ scim2 query serviceproviderconfig > service-provider-config.json

The ``schemas.json`` and ``resource-types.json`` files hold a ``ListResponse``, or a bare list of objects.

Load the files
--------------

Pass the files with the options, or with the
:ref:`SCIM_CLI_SCHEMAS <scim2-schemas-scim_cli_schemas>`,
:ref:`SCIM_CLI_RESOURCE_TYPES <scim2-resource_types-scim_cli_resource_types>` and
:ref:`SCIM_CLI_SERVICE_PROVIDER_CONFIG <scim2-service_provider_config-scim_cli_service_provider_config>`
environment variables:

.. code-block:: console

    $ export SCIM_CLI_SCHEMAS=schemas.json
    $ export SCIM_CLI_RESOURCE_TYPES=resource-types.json
    $ export SCIM_CLI_SERVICE_PROVIDER_CONFIG=service-provider-config.json
    $ scim2 query user

When the configuration of the server changes, save the files again.
Unset the variables first: the shell empties ``schemas.json`` before ``scim2`` reads it.

.. code-block:: console

    $ unset SCIM_CLI_SCHEMAS SCIM_CLI_RESOURCE_TYPES SCIM_CLI_SERVICE_PROVIDER_CONFIG
