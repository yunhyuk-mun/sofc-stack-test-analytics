"""시드 20개로 분류 정확도 분포 확인 (규칙이 시뮬레이터에 맞춰진 순환 검증임을 감안해 보는 용도)."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
from simulate import make
from analyze import stack_features, judge, classify

accs = []; by_rig = {"R1": [], "R2": [], "R3": []}
for seed in range(100, 120):
    df, gt = make(seed)
    f = classify(judge(stack_features(df))).merge(gt, on=["stack", "rig"])
    ok = ((f.cause == f.fault.replace("none", "none")) | ((f.cause == "rig_suspect") & (f.fault == "none")))
    for rg, g in f.assign(ok=ok).groupby("rig"): by_rig[rg].append(float(g.ok.mean()))
    accs.append(float(((f.cause == f.fault.replace("none", "none")) | ((f.cause == "rig_suspect") & (f.fault == "none"))).mean()))
print("seeds=20 acc min/mean/max = %.3f / %.3f / %.3f" % (min(accs), np.mean(accs), max(accs)))
print("호기별 정확도 평균:", {k: round(float(np.mean(v)), 3) for k, v in by_rig.items()})
