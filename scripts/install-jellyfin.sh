#!/usr/bin/env bash
# Sideload Jellyfin on a Tizen TV that already has Developer Mode ON (host IP = this machine).
set -e
TV=${1:-${TV_IP:?set TV_IP or pass the TV address}}
docker info >/dev/null 2>&1 || { echo "Docker daemon not running (macOS: brew install colima && colima start)"; exit 1; }
docker run --rm georift/install-jellyfin-tizen "$TV"
curl -s -m 5 "http://$TV:8001/api/v2/applications/AprZAARz4r.Jellyfin"; echo
