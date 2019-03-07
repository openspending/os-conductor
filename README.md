# OS Conductor

[![Gitter](https://img.shields.io/gitter/room/openspending/chat.svg)](https://gitter.im/openspending/chat)
[![Travis](https://img.shields.io/travis/openspending/os-conductor.svg)](https://travis-ci.org/openspending/os-conductor)
[![Coveralls](http://img.shields.io/coveralls/openspending/os-conductor/master.svg)](https://coveralls.io/r/openspending/os-conductor)
[![Issues](https://img.shields.io/badge/issue-tracker-orange.svg)](https://github.com/openspending/openspending/issues)
[![Docs](https://img.shields.io/badge/docs-latest-blue.svg)](http://docs.openspending.org/)

Web services for OpenSpending, responsible for:

- user authentication, identity and access control
- package upload, management, and status
- package search of os-package-registry
- upload to the S3 datastore

os-conductor uses [Flask](http://flask.pocoo.org/) web framework.

## Quick start for development

Clone the repo, install dependencies from pypi, and run the server. See the [docs](http://docs.openspending.org/en/latest/developers/conductor/) for more information.

The `os-types` node utility is used to perform fiscal modelling for the processed datapackage. To install, use npm:

`$ npm install -g os-types`

### Tests

With a running ElasticSearch server available on localhost:9200:

```
$ pip install tox  # install tox
$ tox
```

### Environmental Variables

OS Conductor requires environmental variables to be set, either in the local environment or in a `.env` file in the root directory.

```ini
# Required settings

# Base URL for the application, e.g. 'http://localhost' or 'https://openspending.org'
OS_BASE_URL=
# Address for the postgres instance, e.g. postgresql://postgres@db/postgres
OS_CONDUCTOR_ENGINE=
# Address for ElasticSearch instance
OS_ELASTICSEARCH_ADDRESS=

# OAuth credentials. See the OAuth Credentials section below for details.
OS_CONDUCTOR_SECRETS_0=
OS_CONDUCTOR_SECRETS_1=
OS_CONDUCTOR_SECRETS_2=
OS_CONDUCTOR_SECRETS_3=

# AWS S3 credentials
OS_ACCESS_KEY_ID=
OS_SECRET_ACCESS_KEY=
OS_S3_HOSTNAME=
OS_STORAGE_BUCKET_NAME=

# Optional settings

# Address for memcached server, e.g. http://cache:11211
OS_CONDUCTOR_CACHE=

# Address for the redis os-api-cache server, e.g. redis
OS_API_CACHE=

# If this env var exists, the entrypoint script will check whether ElasticSearch is healthy before allowing os-conductor to start.
OS_CHECK_ES_HEALTHY=

# If using the fake-s3 docker container for development, openspending/fakes3, add these settings:
USE_FAKE_S3=True
OS_S3_PORT=4567
```

### OAuth Credentials

OS Conductor needs credentials for authentication and authorization tasks. Credential values is set on `OS_CONDUCTOR_SECRETS_<n>` env vars. We provide a python script to help generate these values in `docker/secrets/generate-secrets/to_env_vars.py`.

1. Create a [Google OAuth Credentials](https://console.developers.google.com/apis/credentials) and retain the Client ID and Secret Key
2. Paste the Client ID and Secret Key values in to `google.key` and `google.secret.key` files respectively within the `generate-secrets` directory.
3. Run the python script:

```bash
$ cd docker/secrets/generate-secrets
$ python ./to_env_vars.py
```

4. Copy the generated env var key/values into your local environment or `.env` file in the root directory.


### Admin tools

Various admin tools are available in the `/tools` directory. Some tools require dependencies to be installed from `/tools/requirements.txt`.

#### `remove_package.py`

Remove a named package (or packages) from the ElasticSearch index, and hence from searches and discovery within OpenSpending. Removing a package from the index won't remove it from the AWS datastore.


## API Endpoints

Conductor current ships with the following blueprints, and their API endpoints.

### Get authorized upload URL(s)
`/datastore/authorize`

**Method:** `POST`

**Query Parameters:**

 - `jwt` - permission token (received from `/user/authorize`)

**Headers:**

 - `Auth-Token` - permission token (can be used instead of the `jwt` query parameter)

**Body:**

JSON content with the following structure:
```js
{
    "metadata": {
        "owner": "<user-id-of-uploader>",
        "name": "<data-set-unique-id>"
    },
    "filedata": {
        "<relative-path-to-file-in-package-1>": {
            "length": 1234, // length in bytes of data
            "md5": "<md5-hash-of-the-data>",
            "type": "<content-type-of-the-data>",
            "name": "<file-name>"
        },
        "<relative-path-to-file-in-package-2>": {
            "length": 4321,
            "md5": "<md5-hash-of-the-data>",
            "type": "<content-type-of-the-data>",
            "name": "<file-name>"
        }
        ...
    }
}
```

`owner` must match the `userid` that is in the authentication token.

### Get information regarding the datastore
`/datastore/info`

**Method:** `GET`

**Query Parameters:**

 - `jwt` - permission token (received from `/user/authorize`)

**Headers:**

 - `Auth-Token` - permission token (can be used instead of the `jwt` query parameter)

**Returns:**

JSON content with the following structure:
```js
{
    "prefixes": [
        "https://datastore.openspending.org/123456789",
        ...
    ]
}
```

`prefixes` is the list of possible prefixes for an uploaded file for this user.


### Load a datastore package into the OpenSpending DB
`/package/upload`

**Method:** `POST`

**Query Parameters:**

 - `jwt` - permission token (received from `/user/authorize`)
 - `datapackage` - URL of the Fiscal DataPackage to load

### Check on the status of uploading a package to the OpenSpending DB
`/package/status`

**Method:** `GET`

**Query Parameters:**

 - `datapackage` - URL of the Fiscal DataPackage being loaded

**Returns:**

```json
{
    "status": "<status-code>",
    "progress": 123,
    "error": "<error-message-if-applicable>"
}
```

 - `status-code`: one of the following:
    - `queued`: Waiting in queue for an available processor
    - `initializing`: Getting ready to load the package
    - `loading-datapackage`: Reading the Fiscal Data Package
    - `validating-datapackage`: Validating Data Package correctness
    - `loading-resource`: Loading Resource data
    - `deleting-table`: Clearing previous rows for this dataset from the database
    - `creating-table`: Preparing space for rows in the database
    - `loading-data-ready`: Starting to load rows to database
    - `loading-data`: Loading data into the database
    - `creating-babbage-model`: Converting the Data Package into an API model
    - `saving-metadata`: Saving package metadata
    - `done`: Done
    - `fail`: Failed
 - `progress`: # of records loaded so far

Wil return an `HTTP 404` if the package is not being loaded right now.

### Toggle or set a package's privacy setting
`/package/publish`

**Method:** `POST`

**Query Parameters:**

 - `jwt` - permission token (received from `/user/authorize`)
 - `id` - Unique identifier of the datapackage to modify
 - `publish` - Publishing status, either:
    - `true`: force publish,
    - `false`: force private,
    - `toggle`: toggle the state

**Returns:**

```js
{
    "success": true,
    "published": true  // or false
}
```

### Search for specific packages
`/search/package`

**Method:** `GET`

**Query Parameters:**

 - `jwt` - authentication token (received from `/user/check`)
 - `q` - match-all query string
 - `package.title` - filter by package title
 - `package.author` - filter by package author
 - `package.description` - filter by package description
 - `package.regionCode` - filter by package region code
 - `package.countryCode` - filter by package region code
 - `package.packageCode` - filter by package region code
 - `size` - number of results to return

All values for all parameters (except `jwt`) should be passed as JSON values.

**Returns:**

All packages that match the filter.

If authentication-token was provided, then private packages from the authenticated user will also be included.
Otherwise, only public packages will be returned.

```js
[
    {
        "id": "<package-unique-id>",
        "model": { ... }, // Babbage model
        "package": { .... }, // Original FDP
        "origin_url": "<url-to-the-datapackage.json>"
    }
]
```

### Check an authentication token's validity
`/user/check`

**Method:** `GET`

**Query Parameters:**

 - `jwt` - authentication token
 - `next` - URL to redirect to when finished authentication

**Returns:**

If authenticated:

```js
{
    "authenticated": true,
    "profile": {
        "id": "<user-id>",
        "name": "<user-name>",
        "email": "<user-email>",
        "avatar_url": "<url-for-user's-profile-photo>",
        "idhash": "<unique-id-of-the-user>",
        "username": "<user-selected-id>" // If user has a username
    }
}
```

If not:

```js
{
    "authenticated": false,
    "providers": {
        "google": {
            "url": "<url-for-logging-in-with-the-Google-provider>"
        }
    }
}
```

When the authentication flow is finished, the caller will be redirected to the `next` URL with an extra query parameter
`jwt` which contains the authentication token. The caller should cache this token for further interactions with the API.

### Get permission for a service
`/user/authorize`

**Method:** `GET`

**Query Parameters:**

 - `jwt` - user token (received from `/user/check`)
 - `service` - the relevant service (e.g. `os.datastore`)

**Returns:**

```js
{
    "token": "<token-for-the-relevant-service>"
    "userid": "<unique-id-of-the-user>",
    "permissions": {
        "permission-x": true,
        "permission-y": false
    },
    "service": "<relevant-service>"
}
```

__Note__: as of yet: the `permissions` property is still returned empty. Real permissions will be implemented soon.

### Change the username
`/user/update`

**Method:** `POST`

**Query Parameters:**

 - `jwt` - authentication token (received from `/user/check`)
 - `username` - A new username for the user profile (this action is only allowed once)

**Returns:**

```js
{
    "success": true,
    "error": "<error-message-if-applicable>"
}
```

__Note__: trying to update other user profile fields like `email` will fail silently and return

```js
{
    "success": true
}
```

### Receive authorization public key
`/user/public-key`

**Method:** `GET`

**Returns:**

The conductor's public key in PEM format.

Can be used by services to validate that the permission token is authentic.

### Read authentication JS library
`/user/lib`

**Method:** `GET`

**Returns:**

Authentication Javascript library with Angular 1.x binding.
