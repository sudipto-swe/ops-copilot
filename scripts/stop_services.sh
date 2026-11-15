#!/usr/bin/env bash
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$DIR"

echo "Stopping services..."
if [ -d .pids ]; then
  for pidfile in .pids/*.pid; do
    if [ -f "$pidfile" ]; then
      pid=$(cat "$pidfile")
      kill "$pid" 2>/dev/null || true
      rm -f "$pidfile"
    fi
  done
fi

pkill -f "uvicorn target\." 2>/dev/null || true
pkill -f "uvicorn apps\.api" 2>/dev/null || true
echo "All stopped."
