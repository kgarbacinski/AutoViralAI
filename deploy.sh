#!/bin/bash

# One-time server initialization for AutoViralAI
# Continuous deployment is handled by GitHub Actions (push to main)
#
# Usage: SSH_HOST=my.server.com SSH_USER=root SSH_PORT=22 ./deploy.sh
#
# Uploads .env (secrets) to the server as agent.env and links it as .env,
# which docker compose reads. Run once before the first deploy, or when secrets change.

set -e

# --- Configuration ---
: "${SSH_HOST:?Set SSH_HOST (your server hostname or IP)}"
SSH_USER="${SSH_USER:-root}"
SSH_PORT="${SSH_PORT:-22}"
REMOTE_DIR="${REMOTE_DIR:-/root/autoviralai}"

# --- Preflight checks ---
if [ ! -f ".env" ]; then
    echo "Error: .env file not found. Copy .env.example and fill in your values."
    exit 1
fi

echo "Creating remote directory..."
ssh -p "$SSH_PORT" "${SSH_USER}@${SSH_HOST}" "mkdir -p ${REMOTE_DIR}"

echo "Uploading .env as agent.env (secrets)..."
scp -P "$SSH_PORT" .env "${SSH_USER}@${SSH_HOST}:${REMOTE_DIR}/agent.env"
ssh -p "$SSH_PORT" "${SSH_USER}@${SSH_HOST}" \
    "chmod 600 ${REMOTE_DIR}/agent.env && ln -sf ${REMOTE_DIR}/agent.env ${REMOTE_DIR}/.env"

echo ""
echo "Server initialized!"
echo "Push to main — GitHub Actions will build and deploy automatically."
