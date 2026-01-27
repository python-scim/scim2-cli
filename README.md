# scim2-cli

An utility command line to help you perform requests against a SCIM server, while validating input and response payloads. It also uses [scim2-tester](https://scim2-tester.readthedocs.io) to perform a [SCIM server compliance test](https://scim2-cli.readthedocs.io/en/latest/reference.html#scim-url-test).

## What's SCIM anyway?

SCIM stands for System for Cross-domain Identity Management, and it is a provisioning protocol.
Provisioning is the action of managing a set of resources across different services, usually users and groups.
SCIM is often used between Identity Providers and applications in completion of standards like OAuth2 and OpenID Connect.
It allows users and groups creations, modifications and deletions to be synchronized between applications.

## Features

- **CRUD Commands**: `create`, `query`, `replace` and `delete` resources from the command line
- **Search Command**: Query resources using SCIM filters, sorting and pagination
- **Compliance Testing**: Built-in `test` command using [scim2-tester](https://scim2-tester.readthedocs.io) to validate server RFC compliance
- **Server Discovery**: Automatic retrieval of server schemas and resource types
- **Dynamic CLI Options**: Command options generated from server schemas
- **Flexible Input**: Pass attributes as CLI options or pipe JSON payloads via stdin
- **JSON Output**: Formatted JSON responses with optional indentation control
- **Authentication**: Custom HTTP headers support for Bearer tokens and other auth methods

## Installation

```console
$ curl -LsSf uvx.sh/scim2-cli/install.sh | sh
```

Check the [installation documentation](https://scim2-cli.readthedocs.io/en/latest/installation.html) for other methods.

## Usage

Check the [reference](https://scim2-cli.readthedocs.io/en/latest/reference.html) for more details.

Here is an example of resource creation:

```console
$ scim2 --url https://auth.example --header "Authorization: Bearer 12345" create user --user-name "bjensen@example.com"
{
    "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
    "id": "2819c223-7f76-453a-919d-413861904646",
    "userName": "bjensen@example.com",
    "meta": {
        "resourceType": "User",
        "created": "2010-01-23T04:56:22Z",
        "lastModified": "2011-05-13T04:42:34Z",
        "version": 'W\\/"3694e05e9dff590"',
        "location": "https://example.com/v2/Users/2819c223-7f76-453a-919d-413861904646",
    },
}
```

Here is an example of resource query:

```console
$ scim2 --url https://auth.example --header "Authorization: Bearer 12345" query user 2819c223-7f76-453a-919d-413861904646
{
    "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
    "id": "2819c223-7f76-453a-919d-413861904646",
    "userName": "bjensen@example.com",
    "meta": {
        "resourceType": "User",
        "created": "2010-01-23T04:56:22Z",
        "lastModified": "2011-05-13T04:42:34Z",
        "version": 'W\\/"3694e05e9dff590"',
        "location": "https://example.com/v2/Users/2819c223-7f76-453a-919d-413861904646",
   }
}
```

scim2-cli belongs in a collection of SCIM tools developed by [Yaal Coop](https://yaal.coop),
with [scim2-models](https://github.com/python-scim/scim2-models),
[scim2-client](https://github.com/python-scim/scim2-client) and
[scim2-tester](https://github.com/python-scim/scim2-tester)
