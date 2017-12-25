import os

# Private/Public key pair
# -- use tools/generate_key_pair.sh to generate a key pair
private_key = os.environ.get('PRIVATE_KEY')
public_key = os.environ.get('PUBLIC_KEY')

# Google Secrets
google_key = os.environ.get('GOOGLE_KEY')
google_secret = os.environ.get('GOOGLE_SECRET')

# Github Secrets
github_key = os.environ.get('GITHUB_KEY')
github_secret = os.environ.get('GITHUB_SECRET')

# Database connection string
db_connection_string = os.environ.get('DATABASE_URL')

# Allowed services
allowed_services = os.environ.get('ALLOWED_SERVICES', '').split(';')
if '' in allowed_services:
    allowed_services.remove('')
allowed_services = dict(
    (p[0], p[1] if len(p) > 1 else p[0])
    for p in map(
        lambda s: s.split(':', 1),
        allowed_services
    )
)