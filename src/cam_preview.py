"""카메라 미리보기 + 장면 찍기 (4단계 자료 준비용, 원문에 없음).
저장소 루트에서 실행: python src/cam_preview.py [--usb 0] [--port 8090]
맥 브라우저에서 http://<보드 Tailscale IP>:8090 → 방향을 맞추고 이름을 넣어 [찍기] → media/<이름>.jpg

- 보드 모니터는 다른 계정의 데스크톱 세션이라 쓰지 않는다. 브라우저로 본다.
- 강의실 영상이라 Tailscale 주소에만 연다 (교육장 LAN에 열지 않는다).
- 웹캠의 MJPEG 패킷을 디코딩 없이 그대로 보낸다 (CPU를 거의 안 쓴다).
"""
import argparse
import re
import subprocess
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import av

ap = argparse.ArgumentParser()
ap.add_argument("--usb", type=int, default=0)
ap.add_argument("--port", type=int, default=8090)
args = ap.parse_args()

latest = {"jpg": None}
cond = threading.Condition()


def capture():
    cam = av.open(f"/dev/video{args.usb}", format="v4l2",
                  options={"input_format": "mjpeg", "video_size": "640x480", "framerate": "15"})
    for pkt in cam.demux(cam.streams.video[0]):
        if pkt.size:
            with cond:
                latest["jpg"] = bytes(pkt)
                cond.notify_all()


PAGE = """<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>카메라 미리보기</title>
<body style="font-family:sans-serif;margin:16px">
<img src="/stream" style="max-width:100%;border:1px solid #888"><p>
<form onsubmit="fetch('/snap?name='+encodeURIComponent(n.value)).then(r=>r.text()).then(t=>{log.textContent=t+'\\n'+log.textContent});return false">
장면 이름 <input id="n" placeholder="whiteboard" required> <button>찍기</button></form>
<pre id="log"></pre></body>"""


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_GET(self):
        u = urlparse(self.path)
        if u.path == "/":
            body = PAGE.encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(body)
        elif u.path == "/stream":
            self.send_response(200)
            self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=f")
            self.end_headers()
            try:
                while True:
                    with cond:
                        cond.wait(timeout=2)
                        jpg = latest["jpg"]
                    if jpg:
                        self.wfile.write(b"--f\r\nContent-Type: image/jpeg\r\n\r\n" + jpg + b"\r\n")
            except (BrokenPipeError, ConnectionResetError):
                pass
        elif u.path == "/snap":
            name = re.sub(r"[^\w-]", "_", parse_qs(u.query).get("name", ["scene"])[0])[:40]
            jpg = latest["jpg"]
            Path("media").mkdir(exist_ok=True)
            Path(f"media/{name}.jpg").write_bytes(jpg)
            msg = f"saved media/{name}.jpg ({len(jpg)//1024} KB)"
            print(msg, flush=True)
            self.send_response(200)
            self.end_headers()
            self.wfile.write(msg.encode())
        else:
            self.send_response(404)
            self.end_headers()


ts_ip = subprocess.run(["tailscale", "ip", "-4"], capture_output=True, text=True).stdout.split()[0]
threading.Thread(target=capture, daemon=True).start()
print(f"open http://{ts_ip}:{args.port}", flush=True)
ThreadingHTTPServer((ts_ip, args.port), H).serve_forever()
