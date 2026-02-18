#!/bin/bash

# One-time server initialization for threads-agent on Mikrus
# Continuous deployment is handled by GitHub Actions (push to main)
#
# Usage: ./deploy.sh
#
# This script uploads .env and docker-compose.prod.yml to the server.
# Run this once before the first GitHub Actions deploy, or whenever
# you need to update server-side configs (.env changes, compose changes).

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

if [ ! -f "docker-compose.prod.yml" ]; then
    echo "Error: docker-compose.prod.yml not found."
    exit 1
fi

echo "Creating remote directory..."
ssh -p $SSH_PORT ${SSH_USER}@${SSH_HOST} "mkdir -p ${REMOTE_DIR}"

echo "Uploading .env..."
scp -P $SSH_PORT .env ${SSH_USER}@${SSH_HOST}:${REMOTE_DIR}/.env

echo "Uploading docker-compose.prod.yml as docker-compose.yml..."
scp -P $SSH_PORT docker-compose.prod.yml ${SSH_USER}@${SSH_HOST}:${REMOTE_DIR}/docker-compose.yml

echo ""
echo "Server initialized!"
echo ""
echo "Next steps:"
echo "  1. Add your SSH private key as GitHub Secret 'SSH_PRIVATE_KEY'"
echo "  2. Push to main — GitHub Actions will build, upload, and deploy automatically"
echo ""
echo "To update .env or compose config, re-run this script."
