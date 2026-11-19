"""열화 탐지의 노이즈 민감도. 이벤트가 있는 데이터(검출률)와 없는 데이터(오경보율)를 시드 30개씩 돌린다.
임계값(STEP_MV 등)은 노이즈 1.5 mV 기준으로 정한 가정값이라, 노이즈가 커지면 어떻게 되는지 직접 확인한다."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np, pandas as pd
from degradation import simulate, detect
OUT = os.path.join(os.path.dirname(__file__), "..", "out")
rows = []
for noise_mV in (1.5, 3, 5, 8):
    hit_step = hit_acc = fa = 0; err = []
    for seed in range(30):
        _, _, _, ev = detect(simulate(seed, noise=noise_mV / 1000, events=True))
        types = [e["type"] for e in ev]
        s = [e for e in ev if e["type"] == "step_drop"]
        hit_step += bool(s and abs(s[0]["hour"] - 1100) <= 50)
        hit_acc += "accelerated_degradation" in types
        _, _, _, ev0 = detect(simulate(1000 + seed, noise=noise_mV / 1000, events=False))
        fa += bool(ev0)
        deg0, *_ = detect(simulate(seed, noise=noise_mV / 1000, events=True)); err.append(deg0)
    rows.append(dict(noise_mV=noise_mV, step_detect=f"{hit_step}/30", accel_detect=f"{hit_acc}/30",
                     false_alarm_clean=f"{fa}/30", base_rate_mean=round(np.mean(err), 2), base_rate_sd=round(np.std(err), 2)))
r = pd.DataFrame(rows); r.to_csv(f"{OUT}/noise_sweep.csv", index=False); print(r.to_string(index=False))
