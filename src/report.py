"""스택별 시험 성적서와 평가 이력표를 자동 생성한다. (시뮬레이션 스택 데이터)
성적서: 시험 조건, 판정 항목별 측정값과 기준, 최종 판정, 이상 시 점검 순서, 셀 전압 그림.
이력표: 전체 스택의 판정 이력 (out/test_history.csv)."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from analyze import SPEC
plt.rcParams["font.family"] = "Malgun Gothic"; plt.rcParams["axes.unicode_minus"] = False
OUT = os.path.join(os.path.dirname(__file__), "..", "out")
os.makedirs(f"{OUT}/reports", exist_ok=True)
g = pd.read_csv(f"{OUT}/guard_band_result.csv"); data = pd.read_csv(f"{OUT}/test_data.csv")
CHECK = {"gas_leak": "1) 해당 셀 전압과 이웃 셀 비교 2) 가스 공급·시일 상태 점검 3) 누설 시험 후 재조립 여부 판단",
         "contact_degradation": "1) 해당 셀 열화율 추이 확인 2) 접촉 압력·체결 상태 점검 3) 연료 조건 확인 후 열화 판정",
         "low_performance": "1) 호기 온도·계측 정합성 확인 2) 연료 조성·이용률 확인 3) 동일 조건 재측정",
         "rig_suspect": "1) 같은 호기 다른 스택과 비교 2) 호기 온도 센서·계측기 교정 확인 3) 다른 호기에서 재평가",
         "none": "-"}
hist = g[["stack", "rig", "mean_V", "min_cell_V", "spread", "deg_pct_kh", "worst_deg_pct_kh", "cause", "final"]].copy()
hist.round(4).to_csv(f"{OUT}/test_history.csv", index=False)
pick = []
for c in ("none", "gas_leak", "contact_degradation", "low_performance"):
    r = g[g.cause == c]
    if len(r): pick.append(r.iloc[0])
for r in pick:
    sid = r["stack"]; d = data[data["stack"] == sid]
    fig, ax = plt.subplots(figsize=(6, 3.6))
    for c, gc in d.groupby("cell"): ax.plot(gc.hour, gc.cell_V, lw=.6, color="gray", alpha=.6)
    m = d.groupby("hour").cell_V.mean(); ax.plot(m.index, m.values, "b", lw=2, label="평균")
    if r.cause != "none":
        w = d[d.cell == r.worst_deg_cell if r.cause == "contact_degradation" else d.cell == r.min_cell]
        ax.plot(w.hour, w.cell_V, "r", lw=2, label="이상 의심 셀")
    ax.set_xlabel("시간 [h]"); ax.set_ylabel("셀 전압 [V]"); ax.legend(); ax.set_title(f"{sid} 셀 전압 (시뮬레이션)")
    fig.tight_layout(); fig.savefig(f"{OUT}/reports/{sid}.png", dpi=120); plt.close(fig)
    with open(f"{OUT}/reports/{sid}.md", "w", encoding="utf-8") as f:
        f.write(f"# 시험 성적서 {sid} (시뮬레이션 데이터)\n\n호기 {r.rig} | 시험 전류밀도 0.4 A/cm² | 500 h | 셀 30개\n\n")
        f.write("| 항목 | 측정값 | 기준 | 결과 |\n|---|---|---|---|\n")
        f.write(f"| 초기 평균 셀전압 | {r.mean_V:.3f} V | {SPEC['mean_V_min']} V 이상 | {r.mean_zone} |\n")
        f.write(f"| 초기 최저 셀전압 | {r.min_cell_V:.3f} V (셀 {int(r.min_cell)}) | {SPEC['cell_V_min']} V 이상 | {r.cell_zone} |\n")
        f.write(f"| 셀간 편차 | {r.spread*1000:.0f} mV | {SPEC['spread_max']*1000:.0f} mV 이하 | {'PASS' if r.pass_spread else 'FAIL'} |\n")
        f.write(f"| 스택 열화율 | {r.deg_pct_kh:.2f} %/kh | {SPEC['deg_max_pct_kh']} %/kh 이하 | {'PASS' if r.pass_deg else 'FAIL'} |\n")
        f.write(f"| 최악 셀 열화율 | {r.worst_deg_pct_kh:.2f} %/kh (셀 {int(r.worst_deg_cell)}) | {SPEC['worst_cell_deg_max']} %/kh 이하 | {'PASS' if r.pass_worst else 'FAIL'} |\n\n")
        f.write(f"**최종 판정: {r.final}**  원인 분류: {r.cause}\n\n점검 순서: {CHECK[r.cause]}\n\n![셀 전압]({sid}.png)\n\n")
        f.write("기준값은 가정값이며 측정 불확도 약 2 mV(k=2)를 반영한 판정입니다. 실제 양산 성적서가 아닙니다.\n")
print([r["stack"] for r in pick], len(hist))
