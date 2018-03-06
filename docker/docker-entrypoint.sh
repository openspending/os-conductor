#!/bin/bash
set -e

# This script is the entrypoint to the os-conductor Docker container. This will
# verify that the Elasticsearch environment variable is set and that
# Elasticsearch is running before executing the command provided to the docker
# container.

# Read parameters from the environment and validate them.
checkHost() {
    if [ -z "$$1" ]; then
        echo >&2 'Error: missing required $1 environment variable'
        echo >&2 '  Did you forget to -e $1=... ?'
        exit 1
    fi
}

readParams() {
  checkHost "OS_ELASTICSEARCH_ADDRESS"
}

# Wait for elasticsearch to start. It requires that the status be either green
# or yellow.
waitForElasticsearch() {
  echo -n "Waiting on $1 to start."
  for ((i=1;i<=300;i++))
  do
    health=$(curl --silent "http://$1/_cat/health" | awk '{print $4}')
    if [[ "$health" == "green" ]] || [[ "$health" == "yellow" ]]
    then
      echo
      echo "Elasticsearch is ready!"
      return 0
    fi

    ((i++))
    echo -n '.'
    sleep 1
  done

  echo
  echo >&2 'Elasticsearch is not running or is not healthy.'
  echo >&2 "Address: ${OS_ELASTICSEARCH_ADDRESS}"
  echo >&2 "$health"
  exit 1
}

# Main
readParams
waitForElasticsearch $OS_ELASTICSEARCH_ADDRESS
exec "$@"
