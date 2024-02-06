#/bin/bash

set -o errexit
set -o pipefail

# Make sure that django's `collectstatic` has been run locally before pushing up to any environment,
# so that the styles and static assets to show up correctly on any environment.

# Default command
cmd="gunicorn --worker-class=gevent registrar.config.wsgi -t 60"

# Check if --bind argument is provided
if [[ "$#" -eq 1 && "$1" == "--bind"* ]]; then
    # Append the provided bind argument to the command
    cmd="$cmd $1"
fi

# Execute the command
eval "$cmd"
