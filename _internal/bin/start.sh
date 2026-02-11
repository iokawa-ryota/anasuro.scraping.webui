#!/bin/bash

cd "$(dirname "$0")" || exit 1

echo "1. setup check"
python3 bin/setup_check.py
if [ $? -ne 0 ]; then
  echo "setup failed"
  exit 1
fi

echo "2. start server"
python3 app/app.py
