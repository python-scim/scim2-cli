Check the compliance of a server
================================

Use this guide to check that a SCIM server complies with the SCIM specifications, and to read the results.
The :ref:`reference:test` command runs the checks of :doc:`scim2-tester <scim2_tester:index>`:
it creates, edits and deletes resources on the server.
Run it against a test server, not against production data.
:doc:`track-the-checks-that-pass-in-ci` covers the use of the results by another program.

Run the checks
--------------

.. code-block:: console

    $ scim2 test
    Performing a SCIM compliance check on http://localhost:8080 ...
    300 passed (seed 2416347125)

The command fails with the exit code 1 when a check fails.
With ``--strict``, it also fails on deviations from the recommendations of the RFCs.

Read the results
----------------

The command only shows the results that warn or fail, with their reasons.
The last line counts the results that passed, warned, failed and were skipped.

``-v`` shows every result with its reason, and ``-vv`` also shows the data of the results,
such as the responses of the server.
Each result shows the status of the check, its title, and the resource type and the attribute it is about:

.. code-block:: console
   :caption: SCIM compliance test showing every result

    $ scim2 test -v
    Performing a SCIM compliance check on http://localhost:8080 ...
    SUCCESS    service_provider_config_endpoint
    SUCCESS    query_all_resource_types
      Resource types available are: 'User', 'Group'
    SUCCESS    query_resource_type_by_id User
      Successfully accessed the /ResourceTypes/User endpoint.
    ...
    SUCCESS    check_replace_attribute User displayName
      Successfully replaced attribute 'displayName'
    ...
    300 passed (seed 2416347125)

The passing results are green, the deviations from the recommendations of the RFCs are yellow,
the failures are red and the skipped checks are gray.

Replay a run
------------

The checks send generated values, such as user names and email addresses.
Each run generates new values, and prints its seed in the summary at the end.
To send the same values again, for instance to replay a failure, pass the seed with ``--seed``:

.. code-block:: console

    $ scim2 test --seed 2416347125

Select the checks
-----------------

To run only some of the checks, pass their tags with ``--include-tags``.
To skip some checks, pass their tags with ``--exclude-tags``.
Both options can be repeated.
A tag also selects the tags below it: ``crud`` selects ``crud:read`` and ``crud:read:attributes``.
``scim2 test --help`` lists the available tags.

.. code-block:: console

    $ scim2 test --include-tags crud --exclude-tags crud:delete
