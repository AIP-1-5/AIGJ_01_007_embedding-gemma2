"""4단계 테스트 자료 만들기: 카메라에서 10초 녹화(media/clip.mp4) + 2초마다 프레임(media/frame_NN.jpg).
저장소 루트에서 실행:
  python src/grab_clip.py --usb 0     # USB 웹캠 /dev/video0
  python src/grab_clip.py --rtsp      # .env의 RTSP_URL

원문과 다른 점
- 원문은 ffmpeg CLI(`-rtsp_transport tcp ... -c:v libx264`)를 쓴다. 보드의 ffmpeg는 NVIDIA 최소 빌드라
  RTSP 프로토콜과 libx264 인코더가 없다. PyAV(pip 휠, 자체 FFmpeg 포함)로 같은 일을 한다.
- 원문은 RTSP만 다룬다. 우리 실습 카메라는 USB 웹캠(C920)이라 v4l2 입력도 받는다 (MJPG 640x480).
- RTSP 주소는 .env의 RTSP_URL에서만 읽고, 출력·로그에 쓰지 않는다 (계정·비밀번호 포함).
"""
import argparse
import os
import sys
from pathlib import Path

import av

ap = argparse.ArgumentParser()
src_group = ap.add_mutually_exclusive_group(required=True)
src_group.add_argument("--usb", type=int, help="USB 카메라 번호 (/dev/videoN)")
src_group.add_argument("--rtsp", action="store_true", help=".env의 RTSP_URL 사용")
ap.add_argument("--seconds", type=float, default=10.0)
ap.add_argument("--every", type=float, default=2.0, help="프레임 저장 간격(초). 원문: ffmpeg -vf fps=0.5")
ap.add_argument("--prefix", default="frame", help="프레임 파일 이름 앞부분")
args = ap.parse_args()


def read_env(path=".env"):
    env = {}
    for line in Path(path).read_text().splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()
    return env


if args.rtsp:
    url = os.environ.get("RTSP_URL") or read_env().get("RTSP_URL", "")
    if not url.startswith("rtsp://") or "<" in url:
        sys.exit(".env의 RTSP_URL이 비어 있거나 예시 값이다")
    src = av.open(url, options={"rtsp_transport": "tcp", "stimeout": "5000000"}, timeout=10)
else:
    src = av.open(f"/dev/video{args.usb}", format="v4l2",
                  options={"input_format": "mjpeg", "video_size": "640x480", "framerate": "15"})

Path("media").mkdir(exist_ok=True)
vin = src.streams.video[0]
dst = av.open("media/clip.mp4", "w")
vout = dst.add_stream("libx264", rate=round(float(vin.average_rate or 15)))
vout.pix_fmt = "yuv420p"
vout.options = {"preset": "veryfast", "crf": "23"}

t0 = None
next_shot = 0.0
shots = 0
for frame in src.decode(vin):
    if frame.time is None:
        continue
    t0 = frame.time if t0 is None else t0
    t = frame.time - t0
    if t > args.seconds:
        break
    if vout.width == 0:
        vout.width, vout.height = frame.width, frame.height
    for pkt in vout.encode(frame.reformat(format="yuv420p")):
        dst.mux(pkt)
    if t >= next_shot:
        shots += 1
        frame.to_image().save(f"media/{args.prefix}_{shots:02d}.jpg", quality=90)
        next_shot += args.every

for pkt in vout.encode():
    dst.mux(pkt)
dst.close()
src.close()
print(f"clip.mp4 {args.seconds:.0f}s {vout.width}x{vout.height}, {args.prefix} jpg {shots}장")
