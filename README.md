# os-authz-service


[![Travis](https://img.shields.io/travis/openspending/os-authz-service.svg)](https://travis-ci.org/openspending/os-datastore-cli)
[![Coveralls](http://img.shields.io/coveralls/openspending/os-authz-service/master.svg)](https://coveralls.io/r/openspending/os-authz-service)

A simple service to allow whitelisted users to load data to the OpenSpending Datastore.

The service is based on `Flask` microframework running on `Python 3` interpreter.
Development environment is based on `npm/gulp` to serve app usnig `browsersync`.
Deployment process is `CI/CD` based on `Travis` and `Heroku` services.

## Getting Started

To start development process clone repository,
go to repository dir and then install development dependencies
into virtual environments, add pre-commit hook and activate `run`
tool with command:

```
$ source activate.sh
```

## Development

To start development server.
Webapp will be opened in the browser.

```
$ run develop
```

## Configuration

The config system uses 3 sources of settings:
- `config.yml` (static)
- `authz/config.py` (runtime)
- `environment variables` (environ)

From low priority (static) to high priority (environ).

To see the current configuration:
```
$ run config
```

## Reviewing

The project follow the next style guides:
- [Open Knowledge Coding Standards and Style Guide](https://github.com/okfn/coding-standards)
- [PEP 8 - Style Guide for Python Code](https://www.python.org/dev/peps/pep-0008/)

To check the project against Python style guide:
```
$ run review
```
## Testing

To run tests with coverage check:
```
$ run test
```
Coverage data will be in the `.coverage` file.

## Deployment

The project uses continous integration and deployment (CI/CD) approach.

To deploy you only have to push your changes to Github:
- changes will be automatically pulled by CI/CD service
- the project will be builded and tested
- the project will be deployed to Heroku

Deployment to Heroku will be done only on master branch on green builds.

To tweak the process use `.travis.yml` ([reference](http://docs.travis-ci.com/user/customizing-the-build/))
file in the root of the project.

> Initial deployment configuration:
  - create an application on Heroku
  - add environment variables to the application on Heroku:
    - OPENSPENDING_ACCESS_KEY_ID
    - OPENSPENDING_SECRET_ACCESS_KEY
    - OPENSPENDING_STORAGE_BUCKET_NAME
    - API_KEY_WHITELIST
  - check/create corresponding S3 bucket on AWS
  - set buildpack `heroku buildpacks:set -a $APPNAME heroku/python`
  - run `travis setup heroku` to add encrypted key into `.travis.yml`
