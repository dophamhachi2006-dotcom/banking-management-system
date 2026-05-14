#!/usr/bin/env bash
set -e
echo "=== Banking Management System ==="
(cd backend && python app.py) &
BACK_PID=$!
sleep 3
(cd frontend && npm run dev) &
FRONT_PID=$!
trap "kill $BACK_PID $FRONT_PID" EXIT
wait
