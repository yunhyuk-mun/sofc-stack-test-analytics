"""시뮬레이션 생성 -> 분석 -> 그림/표/보고서 -> 주입 결함 대비 검증."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from simulate import make
from analyze import stack_features, judge, classify, SPEC

plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False
OUT = os.path.join(os.path.dirname(__file__), "..", "out")

df, gt = make()
df.to_csv(f"{OUT}/test_data.csv", index=False)
gt.to_csv(f"{OUT}/ground_truth.csv", index=False)

f = classify(judge(stack_features(df)))
f = f.merge(gt[["stack", "fault", "bad_cell"]], on="stack")
f.round(4).to_csv(f"{OUT}/stack_summary.csv", index=False)

# 1) 호기별 초기 평균 전압 분포
fig, ax = plt.subplots(figsize=(6, 4))
for rig, g in f.groupby("rig"):
    ax.scatter(int(rig[1]) + np.random.default_rng(0).normal(0, 0.05, len(g)), g.mean_V, alpha=.7, label=rig)
ax.axhline(SPEC["mean_V_min"], color="r", ls="--", label="하한(가정)"); ax.set_xticks([1,2,3]); ax.set_xticklabels(["R1","R2","R3"])
ax.set_ylabel("초기 셀 평균전압 [V]"); ax.set_title("호기별 성능 분포 (시뮬레이션)"); ax.legend()
fig.tight_layout(); fig.savefig(f"{OUT}/fig_rig.png", dpi=130); plt.close(fig)

# 2) 판정 결과 별 평균전압 트렌드
fig, ax = plt.subplots(figsize=(6, 4))
for sid, g in df.groupby("stack"):
    v = f.loc[f["stack"] == sid, "verdict"].iloc[0]
    m = g.groupby("hour").cell_V.mean()
    ax.plot(m.index, m.values, color="tab:blue" if v == "PASS" else "tab:red", alpha=.35, lw=1)
ax.set_xlabel("시간 [h]"); ax.set_ylabel("스택 평균 셀전압 [V]"); ax.set_title("트렌드: 파랑 PASS / 빨강 FAIL (시뮬레이션)")
fig.tight_layout(); fig.savefig(f"{OUT}/fig_trend.png", dpi=130); plt.close(fig)

# 3) 이상 스택 한 개의 셀별 전압 히트맵
bad = f[f.cause == "gas_leak"]
if len(bad):
    sid = bad.iloc[0]["stack"]
    p = df[df["stack"] == sid].pivot(index="cell", columns="hour", values="cell_V")
    fig, ax = plt.subplots(figsize=(6, 4))
    im = ax.imshow(p.values, aspect="auto", cmap="viridis")
    ax.set_title(f"{sid} 셀별 전압 (시뮬레이션)"); ax.set_xlabel("시간 인덱스"); ax.set_ylabel("셀 번호")
    fig.colorbar(im, label="V"); fig.tight_layout(); fig.savefig(f"{OUT}/fig_cell_heatmap.png", dpi=130); plt.close(fig)

# 4) 주입 결함 대비 원인 분류 정확도
truth_map = {"none": "none", "gas_leak": "gas_leak", "contact_degradation": "contact_degradation",
             "low_performance": "low_performance"}
f["truth"] = f.fault.map(truth_map)
f["ok"] = (f.cause == f.truth) | ((f.cause == "rig_suspect") & (f.truth == "none"))
acc = f.ok.mean()
cm = pd.crosstab(f.truth, f.cause)
cm.to_csv(f"{OUT}/confusion.csv")

# R3 호기 효과: 결함이 없는데 FAIL 난 스택 (호기 문제)
r3_false = f[(f.truth == "none") & (f.verdict == "FAIL")]
print("판정:", f.verdict.value_counts().to_dict())
print("원인 분류 정확도: %.3f" % acc)
print(cm)
print("결함 없는데 FAIL(주로 R3 호기):", r3_false.rig.value_counts().to_dict())
print("누설 셀 번호 적중:", int((f[f.truth == 'gas_leak'].min_cell == f[f.truth == 'gas_leak'].bad_cell).sum()),
      "/", int((f.truth == 'gas_leak').sum()))
with open(f"{OUT}/summary.txt", "w", encoding="utf-8") as fh:
    fh.write(f"verdict={f.verdict.value_counts().to_dict()}\nacc={acc:.3f}\n{cm}\n")
