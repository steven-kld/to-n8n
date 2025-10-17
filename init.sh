#!/bin/sh
set -e

echo "[n8n-init] Running pre-start hook..."

cd /data

if [ -d .git ]; then
  echo "[n8n-init] Pulling latest workflows..."
  git pull --ff-only || echo "[warn] git pull failed"
fi

if [ -d "./n8n_workflows" ]; then
  echo "[n8n-init] Importing workflows..."
  n8n import:workflow --separate --input=./n8n_workflows/ || echo "[warn] import failed"
fi

echo "[n8n-init] Done."
