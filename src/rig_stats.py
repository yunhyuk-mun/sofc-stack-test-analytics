"""호기 효과 통계 (시뮬레이션 스택 60개). 호기 R3의 -12 K 편차는 시뮬레이터가 주입한 값이므로,
이 검정은 "주입한 효과를 통계적으로 구분할 수 있는가"를 보는 것이지 실제 호기 분석이 아니다."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np, pandas as pd
OUT = os.path.join(os.path.dirname(__file__), "..", "out")
f = pd.read_csv(f"{OUT}/stack_summary.csv")
ok = f[f.fault == "none"]                       # 결함 없는 스택만 비교해 교란을 줄인다
rng = np.random.default_rng(0)
rows = []
for a, b in (("R3", "R1"), ("R3", "R2"), ("R1", "R2")):
    x, y = ok[ok.rig == a].mean_V.values, ok[ok.rig == b].mean_V.values
    diff = x.mean() - y.mean()
    pool = np.concatenate([x, y]); n = len(x); cnt = 0
    for _ in range(5000):
        rng.shuffle(pool)
        if abs(pool[:n].mean() - pool[n:].mean()) >= abs(diff): cnt += 1
    se = np.sqrt(x.var(ddof=1) / len(x) + y.var(ddof=1) / len(y))
    rows.append(dict(pair=f"{a}-{b}", n=f"{len(x)}/{len(y)}", diff_mV=diff * 1000,
                     ci95_lo_mV=(diff - 1.96 * se) * 1000, ci95_hi_mV=(diff + 1.96 * se) * 1000, perm_p=(cnt + 1) / 5001))
r = pd.DataFrame(rows).round(3); r.to_csv(f"{OUT}/rig_stats.csv", index=False); print(r.to_string(index=False))
