#!/bin/bash

# One-time server initialization for threads-agent on Mikrus
# Continuous deployment is handled by GitHub Actions (push to main)
#
# Usage: ./deploy.sh
#
# Uploads agent.env (secrets) to the server.
# Run this once before the first deploy, or when secrets change.

set -e

# --- Configuration ---
SSH_HOST="patryk176.mikrus.xyz"
SSH_USER="root"
SSH_PORT="10176"
REMOTE_DIR="/root/threads-agent"

# --- Preflight checks ---
if [ ! -f ".env" ]; then
    echo "Error: .env file not found. Copy .env.example and fill in your values."
    exit 1
fi

echo "Creating remote directory..."
ssh -p $SSH_PORT ${SSH_USER}@${SSH_HOST} "mkdir -p ${REMOTE_DIR}"

echo "Uploading .env as agent.env (secrets)..."
scp -P $SSH_PORT .env ${SSH_USER}@${SSH_HOST}:${REMOTE_DIR}/agent.env
ssh -p $SSH_PORT ${SSH_USER}@${SSH_HOST} "chmod 600 ${REMOTE_DIR}/agent.env"

echo ""
echo "Server initialized!"
echo "Push to main — GitHub Actions will build and deploy automatically."
