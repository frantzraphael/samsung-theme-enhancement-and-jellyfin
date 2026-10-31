#!/usr/bin/env bash
# Discover Samsung Tizen TVs on the local /24 by probing the :8001 info endpoint.
NET=${1:-$(ipconfig getifaddr en0 2>/dev/null | cut -d. -f1-3)}
for i in $(seq 1 254); do (ping -c1 -W 300 "$NET.$i" >/dev/null 2>&1 &); done; sleep 5
for ip in $(arp -an | grep -v incomplete | grep -oE "$NET\.[0-9]+"); do
  r=$(curl -s -m 2 "http://$ip:8001/api/v2/" | grep -oE '"modelName":"[^"]+"')
  [ -n "$r" ] && echo "$ip  $r"
done
