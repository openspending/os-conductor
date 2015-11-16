# os-authz-service

A simple service to allow whitelisted users to load data to the OpenSpending Datastore.

## Development

To start development process clone repository,
go to repository dir and then:
```
nvm use 4
npm install
virtualenv venv
source venv/bin/activate
pip install -r requirements.txt
npm run develop
```
Webapp will be opened in the browser.

Before pushing changes check code style and tests:

```
npm run check
```

## Configuration

The config system uses 3 sources of settings:
- `config.yml` (static)
- `authz/config.py` (runtime)
- `environment variables` (environ)

From low priority (static) to high priority (environ).

To see the current configuration:
```
$ npm run config
```

## Reviewing

The project follow the next style guides:
- [Open Knowledge Coding Standards and Style Guide](https://github.com/okfn/coding-standards)
- [PEP 8 - Style Guide for Python Code](https://www.python.org/dev/peps/pep-0008/)

To check the project against Python style guide:
```
$ npm run review
```
## Testing

To run tests with coverage check:
```
$ npm run test
```
Coverage data will be in the `.coverage` file.

## Deployment

The project uses continous integration and deployment (CI/CD) approach.

To deploy you only have to push your changes to Github:
- changes will be automatically pulled by CI/CD service
- the project will be builded and tested
- the project will be deployed to Heroku

Deployment to Heroku will be done only on master branch on green builds.

To tweak the process use `shippable.yml` ([reference](http://docs.shippable.com/yml_reference/))
file in the root of the project.
