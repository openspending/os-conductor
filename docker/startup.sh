#!/bin/sh
set -e

cd $WORKDIR || cd /app
echo working from `pwd`
echo DB: $OS_CONDUCTOR_ENGINE

echo Setting base url to $OS_BASE_URL
cat conductor/blueprints/user/lib/lib.js | sed 's,https://openspending.org,'"$OS_BASE_URL"',' > lib.js.tmp &&
mv -f lib.js.tmp conductor/blueprints/user/lib/lib.js


gunicorn -w 1 conductor.server:app -b 0.0.0.0:8000
