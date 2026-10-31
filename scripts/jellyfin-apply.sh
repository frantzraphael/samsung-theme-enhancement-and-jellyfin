#!/usr/bin/env bash
# Apply the minimal theme (Custom CSS) and lightweight display settings to ALL users of a Jellyfin server.
# Usage: JF_URL=http://JELLYFIN_HOST:8096 JF_KEY=<api key from Dashboard → API Keys> scripts/jellyfin-apply.sh
set -euo pipefail
: "${JF_URL:?set JF_URL}"; : "${JF_KEY:?set JF_KEY}"
CSS="$(dirname "$0")/../theme/jellyfin-minimal.css"
H="Authorization: MediaBrowser Token=\"$JF_KEY\""
TMP=$(mktemp -d)

echo "== Custom CSS + splash off"
curl -sf -H "$H" "$JF_URL/System/Configuration/branding" > "$TMP/b.json"
python3 - "$TMP/b.json" "$CSS" <<'PY'
import json,sys; b=json.load(open(sys.argv[1])); b["CustomCss"]=open(sys.argv[2]).read(); b["SplashscreenEnabled"]=False
json.dump(b,open(sys.argv[1],"w"))
PY
curl -sf -o /dev/null -H "$H" -H "Content-Type: application/json" -X POST --data-binary @"$TMP/b.json" "$JF_URL/System/Configuration/branding"

echo "== Display preferences per user (client=emby is what jellyfin-web/Tizen use)"
for ID in $(curl -sf -H "$H" "$JF_URL/Users" | python3 -c 'import sys,json; print(" ".join(u["Id"] for u in json.load(sys.stdin)))'); do
  curl -sf -H "$H" "$JF_URL/DisplayPreferences/usersettings?userId=$ID&client=emby" > "$TMP/$ID.json"
  python3 - "$TMP/$ID.json" <<'PY'
import json,sys; p=json.load(open(sys.argv[1])); c=p.setdefault("CustomPrefs",{})
c.update({"enableBackdrops":"false","enableThemeSongs":"false","enableThemeVideos":"false","screensaver":"none",
          "detailsBanner":"false","enableBlurhash":"false",
          "homesection0":"smalllibrarytiles","homesection1":"resume","homesection2":"nextup",
          "homesection3":"none","homesection4":"none","homesection5":"none","homesection6":"none"})
json.dump(p,open(sys.argv[1],"w"))
PY
  curl -sf -o /dev/null -H "$H" -H "Content-Type: application/json" -X POST --data-binary @"$TMP/$ID.json" "$JF_URL/DisplayPreferences/usersettings?userId=$ID&client=emby"
  echo "  user $ID ok"
done
rm -rf "$TMP"; echo "done — restart the Jellyfin app on the TV to reload CSS/preferences"
