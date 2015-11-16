import os
import sys
import authz

# Create application
app = authz.create()

# Port to listen
port = authz.config.SERVER['port']
if len(sys.argv) > 1:
    port = int(sys.argv[1])

# Debug mode
debug = authz.config.DEBUG

# Run application
app.run(port=port, debug=debug)
