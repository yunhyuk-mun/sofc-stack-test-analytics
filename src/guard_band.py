"""측정 불확도를 반영한 판정(guard band).
불확도는 (a) 실측 분극곡선 선형 구간 잔차 RMSE(반복 측정 산포의 대용치, 모델 오차 포함 상한)와
(b) 전압 계측기 정확도 0.5 mV(가정값)를 제곱합 평균해 구하고, 포함인자 k=2를 곱한다.
판정: 값 - U >= 하한 이면 PASS, 값 + U < 하한 이면 FAIL, 그 사이는 재측정."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np, pandas as pd
from load_zenodo import load
from analyze_real import analyze
from analyze import SPEC
OUT = os.path.join(os.path.dirname(__file__), "..", "out")
d = load()
rm = np.mean([analyze(g)[0]["lin_rmse_mV"] for _, g in d.groupby("T_C")])
u = np.sqrt(rm ** 2 + 0.5 ** 2); U = 2 * u / 1000
f = pd.read_csv(f"{OUT}/stack_summary.csv")
def zone(x, lim):
    return np.where(x - U >= lim, "PASS", np.where(x + U < lim, "FAIL", "RETEST"))
f["mean_zone"] = zone(f.mean_V, SPEC["mean_V_min"]); f["cell_zone"] = zone(f.min_cell_V, SPEC["cell_V_min"])
f["final"] = np.where((f.mean_zone == "FAIL") | (f.cell_zone == "FAIL") | (f.verdict == "FAIL") & (f.cause != "none"), "FAIL",
              np.where((f.mean_zone == "RETEST") | (f.cell_zone == "RETEST"), "RETEST", "PASS"))
f.round(4).to_csv(f"{OUT}/guard_band_result.csv", index=False)
print("측정 불확도 U(k=2) = %.2f mV (선형 잔차 %.2f mV 사용)" % (U * 1000, rm))
print("기존 판정", f.verdict.value_counts().to_dict(), "-> guard band 적용", f.final.value_counts().to_dict())
print("재측정 구간 스택:", f[f.final == "RETEST"]["stack"].tolist())
