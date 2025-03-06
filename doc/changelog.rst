Changelog
=========

[0.2.3] - 2025-03-06
--------------------

Added
^^^^^
- Add the ``--no-verify`` parameter to skip certificate verifications. :issue:`20`

[0.2.2] - 2024-12-06
--------------------

Added
^^^^^
- The :ref:`test` command returns 1 in case of errors.
- Added :ref:`test` ``--dont-check-content-type`` and ``--dont-check-status-code`` options.

[0.2.1] - 2024-12-04
--------------------

Added
^^^^^
- Display server discovery step network connections.
- Support loading server configuration objects in :class:`~scim2_models.ListResponses`.

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
