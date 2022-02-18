#!/usr/bin/env sh
# Use wait-for-it wrapped in python to await all necessary services
python ./internals/pre_start_hook.py
uvicorn --host 0.0.0.0 --port 5000 --loop uvloop --workers 16 \
  --no-access-log --log-level warning --no-server-header api:auth_service_rest
