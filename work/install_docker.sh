#!/usr/bin/env bash
set -e
echo "Updating package lists..."
apt-get update
echo "Installing Docker..."
apt-get install -y docker.io
echo "Docker installation completed."