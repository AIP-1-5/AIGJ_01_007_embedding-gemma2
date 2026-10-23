#!/bin/bash
# 6단계: 구성 5개를 차례로 하나씩 올려 측정한다. 구성마다 새 프로세스라 앞 구성의 메모리가 섞이지 않는다.
# 저장소 루트에서, 팀 자물쇠 안에서: ~/practice.sh yj bash src/bench_all.sh
# 결과: runs/bench/<구성>.json (측정값), runs/bench/<구성>.tegra (tegrastats 원본)
set -u
OUT=runs/bench
mkdir -p "$OUT"
for cfg in text image video audio full; do
    tegrastats --interval 500 > "$OUT/$cfg.tegra" &
    TP=$!
    ~/eg2/bin/python src/bench.py "$cfg" 2>/dev/null | tail -1 > "$OUT/$cfg.json"
    kill $TP
    gpu=$(grep -oE 'GR3D_FREQ [0-9]+' "$OUT/$cfg.tegra" | awk '{print $2}' | sort -n | tail -1)
    ram=$(grep -oE 'RAM [0-9]+' "$OUT/$cfg.tegra" | awk '{print $2}' | sort -n | sed -n '1p;$p' | tr '\n' ' ')
    swap=$(grep -oE 'SWAP [0-9]+' "$OUT/$cfg.tegra" | awk '{print $2}' | sort -n | sed -n '1p;$p' | tr '\n' ' ')
    echo "$(cat "$OUT/$cfg.json") | GPU최대 ${gpu}% | 보드RAM 최소/최대 ${ram}MB | 스왑 ${swap}MB"
    sleep 5   # 다음 구성 전에 메모리 반환 대기
done
