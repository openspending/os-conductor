import os
import sys
import authz


# Port to listen
port = authz.config.SERVER['port']
if len(sys.argv) > 1:
    port = int(sys.argv[1])

# Run application
authz.app.run(port=port, debug=authz.config.DEBUG)
