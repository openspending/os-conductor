import os
import sys
import conductor

# Create application
app = conductor.create()

# Port to listen
port = int(conductor.config.PORT)
if len(sys.argv) > 1:
    port = int(sys.argv[1])

# Debug mode flag
debug = conductor.config.DEBUG

# Run application
app.run(host='0.0.0.0', port=port, debug=debug)
