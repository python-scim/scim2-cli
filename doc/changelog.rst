Changelog
=========

[Unreleased]
------------

Changed
^^^^^^^
- scim2-client 0.8.0 and scim2-tester 0.3.0 are now the minimum supported versions.
- Requests are performed with `httpx2 <https://github.com/pydantic/httpx2>`_ instead of
  httpx, following the scim2-client 0.8 engine rename.
- :ref:`reference:query` only sends the ``attributes`` and ``excludedAttributes`` parameters when a
  single resource is queried, as :rfc:`RFC7644 §3.4.1 <7644#section-3.4.1>` defines those
  as the sole parameters of that request. ``--start-index``, ``--count``, ``--filter``,
  ``--sort-by`` and ``--sort-order`` are refused in that case, instead of being sent along.

Fixed
^^^^^
- Server SCIM errors and invalid request payloads are reported as readable messages
  instead of a traceback. scim2-client 0.8 raises the scim2-models exceptions for those,
  which do not belong to its own exception hierarchy.
- The :ref:`reference:test` ``--dont-check-status-code`` and ``--dont-check-content-type`` options
  were not applied on the client.

[0.2.4] - 2026-01-25
--------------------

Added
^^^^^
- Compatibility with scim2-models 0.6

[0.2.3] - 2025-03-06
--------------------

Added
^^^^^
- Add the ``--no-verify`` parameter to skip certificate verifications. :issue:`20`

[0.2.2] - 2024-12-06
--------------------

Added
^^^^^
- The :ref:`reference:test` command returns 1 in case of errors.
- Added :ref:`reference:test` ``--dont-check-content-type`` and ``--dont-check-status-code`` options.

[0.2.1] - 2024-12-04
--------------------

Added
^^^^^
- Display server discovery step network connections.
- Support loading server configuration objects in :class:`~scim2_models.ListResponse`.

[0.2.0] - 2024-12-03
--------------------

.. warning::

   The CLI API have been integraly overhauled

Added
^^^^^
- Python 3.13 support.
- :class:`~scim2_models.Schema`, :class:`~scim2_models.ResourceType` and :class:`~scim2_models.ServiceProviderConfig` are now automatically discovered on the server.
- Available resources are discovered on the server.
- Implement :ref:`SCIM_CLI_URL <scim-url-scim_cli_url>` and :ref:`SCIM_CLI_HEADERS <scim-header-scim_cli_headers>` environment vars.

[0.1.4] - 2024-07-26
--------------------

Fixed
^^^^^
- Use GHA to build binary files.

[0.1.3] - 2024-07-25
--------------------

Fixed
^^^^^
- Dependencies update.

[0.1.2] - 2024-06-05
--------------------

Added
^^^^^
- Add support for passing custom headers to requests.
- Server compliance test.

[0.1.1] - 2024-06-02
--------------------

Added
^^^^^
- Commands to query, search, create, replace, delete

[0.1.0] - 2024-06-01
--------------------

Added
^^^^^
- Initial release
