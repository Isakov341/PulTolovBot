#!/usr/bin/env bash
set -o errexit
apt-get update && apt-get install -y build-essential python3-dev
pip install --upgrade pip
pip install -r requirements.txt
