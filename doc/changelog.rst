Changelog
=========

[0.6.0] - Unreleased
--------------------

Added
^^^^^
- The ``modify`` command sends a PATCH request (:rfc:`7644#section-3.5.2`).
  The operations follow the resource type and the id, and are sent in order:
  ``scim2 modify user 1 replace displayName "Barbara Jensen" remove nickName``.
  Values of string attributes are passed as is, the other values are passed in JSON.
  ``scim2 modify --me`` sends the operations to ``/Me``.
- The ``bulk`` command sends the bulk request passed to stdin (:rfc:`7644#section-3.7`).
  The request is checked against the bulk capabilities of the server before being sent.

[0.5.0] - 2026-10-08
--------------------

Added
^^^^^
- ``--me`` on ``query``, ``create``, ``replace`` and ``delete`` sends the request to ``/Me``,
  the resource of the authenticated client (:rfc:`7644#section-3.11`).
  ``scim2 replace user --me`` needs no ``--id``.
- ``search`` takes an optional resource type. ``scim2 search user`` sends the search to
  ``/Users/.search``.
- ``--cursor`` on ``query`` and ``search``, for cursor-based pagination (:rfc:`9865`).
  An empty value reads the first page. The response gives the cursor of the next page in
  ``nextCursor``.

Changed
^^^^^^^
- The commands are named after the resource types of the server, instead of their models.
  A resource type without a name is named after its id.
  Each resource type has its own command, even when several ones share a schema:
  ``scim2 query employee 1`` reads ``/Employees/1`` next to ``scim2 query user 1``.
  A resource type no longer needs to be named after its schema.
  The resource type can be typed with any case.
- An unknown subcommand of ``create`` and ``replace`` is reported as a usage error.

Fixed
^^^^^
- ``--no-indent`` passed to ``create`` or ``replace`` before the resource type applies.
  It used to be ignored.
- The attributes named ``me``, ``indent`` or ``help`` get the ``--me-attribute``,
  ``--indent-attribute`` and ``--help-attribute`` options in ``create`` and ``replace``.
  They used to collide with the options of the command.
- ``search`` no longer sends empty ``attributes`` and ``excludedAttributes``
  when ``--attribute`` and ``--excluded-attribute`` are not passed.

[0.4.1] - 2026-10-08
--------------------

Added
^^^^^
- A container image is published on the GitHub container registry for each release.

Changed
^^^^^^^
- The code is checked with mypy in strict mode.

Fixed
^^^^^
- ``--no-indent`` prints the JSON response on a single line. It used to print each
  value on its own line.

[0.4.0] - 2026-09-27
--------------------

Changed
^^^^^^^
- Python 3.11 is now the minimum supported version.
- scim2-client 0.9.0 and scim2-tester 0.4.0 are now the minimum supported versions.

Fixed
^^^^^
- What the configuration files leave out is discovered on the server again with
  scim2-client 0.9. Without ``--schemas``, only ``User`` and ``Group`` were known,
  without their extensions. With ``--schemas`` only, the resource types were guessed
  from the schemas.
- ``--resource-types`` without ``--schemas`` no longer crashes.
- A server description whose resource types name unknown schemas is reported as a
  readable error instead of a traceback.

Security
^^^^^^^^
- The control characters of what the server sends are escaped before being displayed, so
  the server cannot rewrite the output on the terminal with escape sequences. This covers
  the :ref:`reference:test` report, the error messages, the subcommand names and the
  option help taken from the schema descriptions.
- The documentation and the :option:`--header <scim --header>` help recommend passing the
  authentication tokens with :ref:`SCIM_CLI_HEADERS <scim-header-scim_cli_headers>`, as other
  users of the machine can see the command line arguments.

[0.3.0] - 2026-09-20
--------------------

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
