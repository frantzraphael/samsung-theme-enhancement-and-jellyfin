#!/usr/bin/env python3
"""Send remote-control keys / text to a Samsung Tizen TV over its WebSocket API.

Pure stdlib (no websocket-client). First run shows an "Allow <name>?" prompt on
the TV; accept it once — the token is saved next to this script and reused.

Usage:
  tvkeys.py [--tv IP] KEY_HOME KEY_ENTER SLEEP1.5 KEY_1 KEY_2 "TEXT:JELLYFIN_HOST:8096"
  tvkeys.py --launch AprZAARz4r.Jellyfin

Tokens: KEY_* (Samsung key codes), SLEEP<seconds>, TEXT:<string> (needs an open IME).
Env: TV_IP (default TV_IP), KEYDELAY seconds between keys (default 0.7).
"""
import argparse, base64, json, os, socket, ssl, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
TOKEN_FILE = os.path.join(HERE, ".tv.token")
APP_NAME = "TizenCtl"


def ws_connect(host, port=8002, timeout=90):
    name = base64.b64encode(APP_NAME.encode()).decode()
    tok = open(TOKEN_FILE).read().strip() if os.path.exists(TOKEN_FILE) else ""
    path = f"/api/v2/channels/samsung.remote.control?name={name}" + (f"&token={tok}" if tok else "")
    ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
    s = ctx.wrap_socket(socket.create_connection((host, port), timeout=10), server_hostname=host)
    key = base64.b64encode(os.urandom(16)).decode()
    s.send((f"GET {path} HTTP/1.1\r\nHost: {host}:{port}\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n").encode())
    hdr = b""
    while b"\r\n\r\n" not in hdr:
        hdr += s.recv(1)
    if b" 101 " not in hdr.split(b"\r\n")[0]:
        sys.exit(f"handshake failed: {hdr.split(b'\r\n')[0]!r}")
    s.settimeout(timeout)
    print("waiting for the TV to accept the connection (first time: press Allow on screen)...", flush=True)
    while True:
        frame = read_frame(s)
        if frame is None:
            sys.exit("connection closed by TV")
        op, data = frame
        if op == 8:
            sys.exit(f"TV closed channel: {data[2:].decode(errors='replace')}")
        if op != 1:
            continue
        msg = json.loads(data)
        ev = msg.get("event")
        if ev == "ms.channel.connect":
            t = msg.get("data", {}).get("token")
            if t:
                open(TOKEN_FILE, "w").write(str(t))
            s.settimeout(5)
            return s
        if ev in ("ms.channel.timeOut", "ms.channel.unauthorized"):
            sys.exit(f"TV refused: {ev}")


def read_frame(s):
    b1 = s.recv(1); b2 = s.recv(1)
    if not b1 or not b2:
        return None
    ln = b2[0] & 0x7F
    if ln == 126:
        ln = int.from_bytes(s.recv(2), "big")
    elif ln == 127:
        ln = int.from_bytes(s.recv(8), "big")
    d = b""
    while len(d) < ln:
        c = s.recv(ln - len(d))
        if not c:
            break
        d += c
    return b1[0] & 0x0F, d


def send_json(s, obj):
    p = json.dumps(obj).encode(); m = os.urandom(4)
    h = bytes([0x81]) + (bytes([0x80 | len(p)]) if len(p) < 126 else bytes([0x80 | 126]) + len(p).to_bytes(2, "big"))
    s.send(h + m + bytes(b ^ m[i % 4] for i, b in enumerate(p)))


def send_key(s, key):
    send_json(s, {"method": "ms.remote.control", "params": {"Cmd": "Click", "DataOfCmd": key,
                                                            "Option": "false", "TypeOfRemote": "SendRemoteKey"}})


def send_text(s, text):
    b64 = base64.b64encode(text.encode()).decode()
    send_json(s, {"method": "ms.remote.control", "params": {"Cmd": b64, "DataOfCmd": "base64", "TypeOfRemote": "SendInputString"}})
    time.sleep(1)
    send_json(s, {"method": "ms.remote.control", "params": {"TypeOfRemote": "SendInputEnd"}})


def launch_app(s, app_id):
    send_json(s, {"method": "ms.channel.emit", "params": {"event": "ed.apps.launch", "to": "host",
                                                          "data": {"appId": app_id, "action_type": "NATIVE_LAUNCH"}}})


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tv", default=os.environ.get("TV_IP"))
    ap.add_argument("--launch", metavar="APP_ID", help="launch an app by id (e.g. AprZAARz4r.Jellyfin)")
    ap.add_argument("tokens", nargs="*")
    a = ap.parse_args()
    if not a.tv:
        ap.error("TV address required: --tv <ip> or TV_IP env")
    delay = float(os.environ.get("KEYDELAY", "0.7"))
    s = ws_connect(a.tv)
    time.sleep(2)
    if a.launch:
        launch_app(s, a.launch); print("launch sent:", a.launch)
    for t in a.tokens:
        if t.startswith("SLEEP"):
            time.sleep(float(t[5:]))
        elif t.startswith("TEXT:"):
            send_text(s, t[5:]); print("text sent:", t[5:])
        else:
            send_key(s, t); print("key sent:", t); time.sleep(delay)
    s.close()


if __name__ == "__main__":
    main()
