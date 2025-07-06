#!/usr/bin/env bash
set -o errexit

pip install --upgrade pip
pip install --upgrade --force-reinstall -r requirements.txt
