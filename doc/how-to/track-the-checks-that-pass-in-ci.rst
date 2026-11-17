Track the checks that pass in CI
================================

Use this guide to run the :ref:`reference:test` command in a CI job on a server that does not comply yet,
and to fail the job only when a check that used to pass does not pass anymore.
It assumes :doc:`check-the-compliance-of-a-server`.

Get the results as JSON
-----------------------

With ``--format jsonl``, the command prints one JSON object per line for each result,
including the results that pass and the skipped checks.
The objects do not hold the description and the data of the results, and ``-v`` has no effect.
The header and the summary go to stderr.

.. code-block:: console

    $ scim2 test --format jsonl --seed 2416347125
    Performing a SCIM compliance check on http://localhost:8080 ...
    {"id": "service_provider_config_endpoint", "title": "service_provider_config_endpoint", "resource_type": null, "attribute": null, "status": "SUCCESS", "outcome": "PASSED", "reason": null, "tags": ["discovery", "service-provider-config"]}
    ...
    {"id": "check_replace_attribute[User][displayName]", "title": "check_replace_attribute", "resource_type": "User", "attribute": "displayName", "status": "SUCCESS", "outcome": "PASSED", "reason": "Successfully replaced attribute 'displayName'", "tags": ["patch:replace"]}
    ...
    300 passed (seed 2416347125)

The ``id`` of a result reads ``title[resource_type][attribute]``, without the trailing empty brackets.
It is unique among the results of a run, unless the server publishes two resource types with the same name,
or two schemas with the same id.
It is stable across versions of scim2-tester, and the changelog of scim2-tester announces each renamed check.

Compare with the expected checks
--------------------------------

Keep the list of the ``id`` that pass in a file, and fail when one of them is missing from a new run.
In this example, ``expected.txt`` is a ``passing.txt`` file from a previous run with the same options:

.. code-block:: console

    $ scim2 test --format jsonl --seed 1 > results.jsonl || true
    $ jq -r 'select(.outcome == "PASSED") | .id' results.jsonl | sort > passing.txt
    $ comm -23 expected.txt passing.txt > regressions.txt
    $ test ! -s regressions.txt

The first command ignores the exit code of :ref:`reference:test`, since the server still fails some checks.
A server that does not answer gives no results, so the comparison fails too.

When a fix makes more checks pass, copy ``passing.txt`` to ``expected.txt``.

Keep the same options
---------------------

The tags and the seed change the results:

- A check of the attributes left out by ``--include-tags`` or ``--exclude-tags`` gives one ``SKIPPED`` result
  per resource type, instead of one result per attribute.
- A check that fails on a whole resource type gives one result for this resource type,
  instead of one result per attribute. Its ``id`` then goes missing from ``passing.txt``.

Generate ``expected.txt`` with the options of the CI job, including ``--seed``.

With the same seed, each run sends the same user names and email addresses.
If a run leaves resources on the server, the next run gets conflicts on these values.
Start each CI run on a new server.
