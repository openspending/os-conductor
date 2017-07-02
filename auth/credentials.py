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
