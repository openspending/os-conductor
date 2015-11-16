import os
import sys
import authz

# Create application
app = authz.create()

# Port to listen
port = int(authz.config.PORT)
if len(sys.argv) > 1:
    port = int(sys.argv[1])

# Debug mode flag
debug = authz.config.DEBUG

# Run application
app.run(host='0.0.0.0', port=port, debug=debug)
