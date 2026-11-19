"""시운전 합·부 판정 기준표 1장. 기준값은 실측 분극 곡선(Zenodo 5763484, 해당 단전지)에서 계산하고,
허용 폭은 이 프로젝트가 정한 가정값이다. 실제 양산 기준이 아니다."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from load_zenodo import load
from analyze_real import analyze
from degradation import simulate, detect, STEP_MV, SLOPE_X, SLOPE_MIN, WIN

plt.rcParams["font.family"] = "Malgun Gothic"; plt.rcParams["axes.unicode_minus"] = False
OUT = os.path.join(os.path.dirname(__file__), "..", "out")

d = load()
ref = {}
for T, g in d.groupby("T_C"):
    p, _ = analyze(g)
    ref[T] = dict(ocv=p["OCV"], v03=float(np.interp(0.3, g.j_A_cm2, g.V)), r=p["R_lin"])
deg0, *_ = detect(simulate())

def T3(f): return " / ".join(f(ref[t]) for t in (700, 750, 800))

rows = [
 ["분극곡선", "OCV (j=0)", T3(lambda r: f"{r['ocv']:.3f}") + " V",
  "기준 -20 mV 이내", "기준 -20 ~ -40 mV: 재측정", "-40 mV 미만: 가스 누설·시일 불량 의심"],
 ["분극곡선", "0.3 A/cm² 전압", T3(lambda r: f"{r['v03']:.3f}") + " V",
  "기준 ±3 %", "±3 ~ 6 %: 재측정", "-6 % 미만: 이상 의심 (아래 R_lin, 형상 확인)"],
 ["분극곡선", "선형 구간 면적저항 R_lin (옴+분극+연료이용 합산)", T3(lambda r: f"{r['r']:.2f}") + " Ω·cm²",
  "기준 x1.15 이하", "x1.15 ~ 1.30: 재측정", "x1.30 초과: 저항 증가. 연료 조성·이용률 먼저 확인 후 접촉·전극 열화 의심"],
 ["분극곡선", "고전류 끝점 직선 이탈", "0 ~ -1 mV (실측)",
  "-5 mV 이내", "-5 ~ -10 mV: 유량 확인", "-10 mV 미만: 농도 손실 의심 (검출 민감도 한계 있음)"],
 ["열화", "기준 열화율 (초기 500 h)", f"{deg0:.2f} %/kh (시뮬레이션)",
  "1.5 %/kh 이하", "1.5 ~ 3 %/kh: 관찰 연장", "3 %/kh 초과: 열화 이상"],
 ["열화", "급강하 (48 h 내 전압 하락)", "-12 mV (시뮬레이션 주입)",
  "-6 mV 이내", "-6 ~ -12 mV: 로그·설비 점검", "-12 mV 초과: 운전 중단 후 원인 분석"],
 ["열화", "롤링 열화율 가속", "3.5 %/kh (시뮬레이션 주입)",
  "기준의 3배 미만", f"기준 3배 이상, 1.5 %/kh 미만", "기준 3배 이상 & 1.5 %/kh 이상: 가속 열화"],
]
cols = ["구분", "항목", "기준값 (700 / 750 / 800 °C)", "합격", "재측정·주의", "이상 의심"]
pd.DataFrame(rows, columns=cols).to_csv(f"{OUT}/decision_table.csv", index=False, encoding="utf-8-sig")

with open(f"{OUT}/decision_table.md", "w", encoding="utf-8") as f:
    f.write("# 시운전 합·부 판정 기준표 (가정값)\n\n")
    f.write("기준값은 Zenodo 5763484 실측 단전지 곡선(H2 50 %/N2 50 %, 3.5 cm² 셀)에서 계산했고, 허용 폭은 가정값입니다.\n\n")
    f.write("| " + " | ".join(cols) + " |\n|" + "---|" * len(cols) + "\n")
    for r in rows: f.write("| " + " | ".join(r) + " |\n")
    f.write("\n열화 행의 기준값은 실측이 아니라 시뮬레이션입니다. 실제 양산 스택에는 자체 기준 곡선으로 다시 계산해야 합니다.\n")

fig, ax = plt.subplots(figsize=(13, 6.2)); ax.axis("off")
t = ax.table(cellText=rows, colLabels=cols, loc="center", cellLoc="left",
             colWidths=[.06, .17, .22, .14, .19, .26])
t.auto_set_font_size(False); t.set_fontsize(8.5); t.scale(1, 2.5)
for (r, c), cell in t.get_celld().items():
    if r == 0: cell.set_facecolor("#2f4b6e"); cell.set_text_props(color="white", weight="bold")
    elif c == 3: cell.set_facecolor("#e3f1e3")
    elif c == 4: cell.set_facecolor("#fff4d6")
    elif c == 5: cell.set_facecolor("#f9dcdc")
ax.set_title("시운전 합·부 판정 기준표  (기준값: 실측 단전지 곡선 / 허용 폭: 가정값 / 열화 행: 시뮬레이션)", fontsize=11)
fig.tight_layout(); fig.savefig(f"{OUT}/decision_table.png", dpi=150)
print(open(f"{OUT}/decision_table.md", encoding="utf-8").read())
