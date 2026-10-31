#!/usr/bin/env bash
# Print the Samsung TV's public device info (no pairing needed).
TV=${1:-${TV_IP:?set TV_IP or pass the TV address}}
curl -s -m 5 "http://$TV:8001/api/v2/" | python3 -c '
import sys, json
d = json.loads(sys.stdin.read(), strict=False)["device"]
for k in ("name","modelName","OS","ip","wifiMac","networkType","PowerState","developerMode","developerIP","firmwareVersion"):
    print(f"{k:16} {d.get(k)}")'
