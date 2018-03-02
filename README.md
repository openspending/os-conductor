# OS Conductor

[![Gitter](https://img.shields.io/gitter/room/openspending/chat.svg)](https://gitter.im/openspending/chat)
[![Travis](https://img.shields.io/travis/openspending/os-conductor.svg)](https://travis-ci.org/openspending/os-conductor)
[![Coveralls](http://img.shields.io/coveralls/openspending/os-conductor/master.svg)](https://coveralls.io/r/openspending/os-conductor)
[![Issues](https://img.shields.io/badge/issue-tracker-orange.svg)](https://github.com/openspending/openspending/issues)
[![Docs](https://img.shields.io/badge/docs-latest-blue.svg)](http://docs.openspending.org/en/latest/developers/conductor/)

A set of integration web services for OpenSpending, responsible for identity, notification, and access control.

## Quick start for development

Clone the repo, install dependencies from pypi, and run the server. See the [docs](http://docs.openspending.org/en/latest/developers/conductor/) for more information.

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
# Address for the OS API service (configured as a 'loader'), e.g. http://os-api-loader:8000
OS_API_URL=

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


