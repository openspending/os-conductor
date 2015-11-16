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
