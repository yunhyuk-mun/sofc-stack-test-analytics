"""분극곡선 해석의 민감도 검증.
(1) 750 °C에서 H2 농도만 바꿨을 때 R_lin이 어떻게 변하는가 -> R_lin을 접촉 저항 지표로 쓸 수 있는가
(2) 선형 구간 시작점 J_LIN을 바꾸면 R_lin과 고전류 끝점 이탈이 얼마나 움직이는가
"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np, pandas as pd, openpyxl
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from load_zenodo import SRC, load

plt.rcParams["font.family"] = "Malgun Gothic"; plt.rcParams["axes.unicode_minus"] = False
OUT = os.path.join(os.path.dirname(__file__), "..", "out")

def sheet(name):
    wb = openpyxl.load_workbook(SRC, data_only=True, read_only=True)
    rows = []
    for i, r in enumerate(wb[name].iter_rows(values_only=True)):
        if i < 8 or r[0] is None or r[3] is None: continue
        rows.append((float(r[0]), float(r[3])))
    return pd.DataFrame(rows, columns=["j", "V"])

def lin(df, jmin):
    m = df.j >= jmin
    if m.sum() < 4: return np.nan, np.nan, np.nan
    s, v0 = np.polyfit(df.j[m], df.V[m], 1)
    res = (df.V[m] - (v0 + s * df.j[m])) * 1000
    return -s, res.iloc[-3:].mean(), np.sqrt((res ** 2).mean())

# (1) H2 농도 의존성 (750 °C)
names = {10: "BC_SP_02_IV_H2_10%_750C", 25: "BC_SP_02_IV_H2_25%_750C", 50: "BC_SP_02_IV_H2_std_750C",
         75: "BC_SP_02_IV_H2_75%_750C", 90: "BC_SP_02_IV_H2_90%_750C"}
rows = []
fig, ax = plt.subplots(1, 2, figsize=(11, 4.2))
for h2, nm in names.items():
    df = sheet(nm)
    jmin = 0.3 if df.j.max() > 0.45 else 0.5 * df.j.max()
    r, top, rm = lin(df, jmin)
    rows.append(dict(H2_pct=h2, n_points=len(df), j_max=round(df.j.max(), 3), OCV=df.V.iloc[0], j_lin_start=round(jmin, 3),
                     R_lin=r, top_dev_mV=top, lin_rmse_mV=rm))
    ax[0].plot(df.j, df.V, "o-", ms=3, label=f"H2 {h2} %")
ax[0].set_xlabel("전류밀도 [A/cm²]"); ax[0].set_ylabel("셀 전압 [V]"); ax[0].legend(); ax[0].grid(alpha=.3)
ax[0].set_title("750 °C, H2 농도별 분극 곡선 (실측)")
h = pd.DataFrame(rows); h.round(4).to_csv(f"{OUT}/h2_dependence.csv", index=False)
ax[1].semilogy(h.H2_pct, h.R_lin, "o-"); ax[1].set_xlabel("H2 농도 [%]"); ax[1].set_ylabel("R_lin [Ω·cm²]")
ax[1].set_title("연료 조성만 바꿔도 R_lin이 크게 변한다"); ax[1].grid(alpha=.3, which="both")
fig.tight_layout(); fig.savefig(f"{OUT}/h2_dependence.png", dpi=140); plt.close(fig)
print(h.round(3).to_string(index=False))

# (2) J_LIN 민감도 (H2 50 %, 3개 온도)
d = load(); rows = []
for T, g in d.groupby("T_C"):
    g2 = g.rename(columns={"j_A_cm2": "j"})[["j", "V"]]
    for jmin in (0.15, 0.2, 0.3, 0.4, 0.5):
        r, top, rm = lin(g2.reset_index(drop=True), jmin)
        rows.append(dict(T_C=T, J_LIN=jmin, R_lin=r, top_dev_mV=top, lin_rmse_mV=rm))
s = pd.DataFrame(rows); s.round(4).to_csv(f"{OUT}/jlin_sensitivity.csv", index=False)
print(s.round(3).to_string(index=False))
