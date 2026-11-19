"""실측 분극 곡선(Zenodo 5763484, CC BY 4.0)의 온도별 비교와 손실 구간 분해.

방법(모델 가정을 최소화한 구간 분해):
 1) 선형 구간: j >= J_LIN 에서 V = V0 - R_lin*j 로 직선 피팅. R_lin은 옴 저항 + 선형 분극저항의 합산 면적저항이다.
    분극 곡선만으로는 옴 저항만 따로 뽑을 수 없다. (분리하려면 EIS가 필요하다.)
 2) 비선형 구간: 직선 아래로 급격히 벗어나는 저전류 구간. 총 손실에서 선형 저항분(R_lin*j)을 뺀 값으로 정의한다. 활성화 손실만이 아니라 OCV 편차와 연료이용에 따른 손실도 포함한다.
 3) 농도 구간: 고전류 끝점 3개가 직선보다 아래로 얼마나 벗어나는지(mV)로 판정한다. 임계값은 가정값이다.
"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from load_zenodo import load

plt.rcParams["font.family"] = "Malgun Gothic"; plt.rcParams["axes.unicode_minus"] = False
OUT = os.path.join(os.path.dirname(__file__), "..", "out")
J_LIN = 0.30            # 선형 구간 시작 전류밀도 [A/cm2]
CONC_FLAG_MV = 5.0      # 고전류 끝점 이탈이 이 값 이상이면 농도 손실 의심 (가정값)
R_GAS = 8.314


def analyze(g):
    j, v = g.j_A_cm2.values, g.V.values
    ocv = v[0]
    m = j >= J_LIN
    slope, v0 = np.polyfit(j[m], v[m], 1)
    r_lin = -slope
    line = v0 + slope * j
    resid_mV = (v - line) * 1000
    top = resid_mV[m][-3:].mean()              # 고전류 끝점 평균 이탈 (음수면 직선 아래)
    rmse = np.sqrt(np.mean(resid_mV[m] ** 2))
    return dict(T_C=int(g.T_C.iloc[0]), OCV=ocv, V0_intercept=v0, R_lin=r_lin, lin_rmse_mV=rmse,
                top_dev_mV=top, conc_suspect=bool(top < -CONC_FLAG_MV),
                j_max=j.max()), line


if __name__ == "__main__":
    d = load(); d.to_csv(f"{OUT}/real_iv_curves.csv", index=False)
    cols = {700: "tab:blue", 750: "tab:green", 800: "tab:red"}
    rows, splits = [], []
    fig, ax = plt.subplots(1, 2, figsize=(11, 4.2))
    for T, g in d.groupby("T_C"):
        p, line = analyze(g)
        rows.append(p)
        ax[0].plot(g.j_A_cm2, g.V, "o", color=cols[T], ms=4, label=f"{T} °C")
        jj = np.linspace(0, g.j_A_cm2.max(), 50)
        ax[0].plot(jj, p["V0_intercept"] - p["R_lin"] * jj, "--", color=cols[T], lw=1)
        for jn in (0.1, 0.3, 0.5):
            if jn <= g.j_A_cm2.max():
                vm = float(np.interp(jn, g.j_A_cm2, g.V))
                total = p["OCV"] - vm
                ohm = p["R_lin"] * jn
                splits.append(dict(T_C=T, j=jn, V=round(vm, 3), total_loss_mV=total * 1000,
                                   ohm_lin_mV=ohm * 1000, act_mV=(total - ohm) * 1000))
    ax[0].set_xlabel("전류밀도 [A/cm²]"); ax[0].set_ylabel("셀 전압 [V]")
    ax[0].set_title("온도별 분극 곡선 (실측: 점, 선형 구간 외삽: 점선)"); ax[0].legend(); ax[0].grid(alpha=.3)
    g = d[d.T_C == 750]; p, _ = analyze(g)
    gg = g[g.j_A_cm2 > 0]
    total = (p["OCV"] - gg.V.values) * 1000
    ohm = p["R_lin"] * gg.j_A_cm2.values * 1000
    ax[1].stackplot(gg.j_A_cm2.values, total - ohm, ohm, labels=["비선형 성분 (총손실 - 선형 저항분)", "선형 구간 저항분 (옴 + 분극 + 연료이용 영향)"],
                    colors=["#e8a33d", "#4a7fb5"])
    ax[1].axvline(J_LIN, color="k", ls=":"); ax[1].text(J_LIN + .01, 10, "선형 구간 시작", fontsize=8)
    ax[1].set_xlabel("전류밀도 [A/cm²]"); ax[1].set_ylabel("전압 손실 [mV]")
    ax[1].set_title("750 °C 손실 구간 분리 (실측 기반, 곡선 형상 기준)"); ax[1].legend(loc="upper left"); ax[1].grid(alpha=.3)
    fig.tight_layout(); fig.savefig(f"{OUT}/real_polarization_loss.png", dpi=140); plt.close(fig)

    pf = pd.DataFrame(rows)
    Tk = pf.T_C.values + 273.15
    ea = np.polyfit(1 / Tk, np.log(pf.R_lin.values), 1)[0] * R_GAS / 1000
    pf.round(4).to_csv(f"{OUT}/real_fit_params.csv", index=False)
    pd.DataFrame(splits).round(1).to_csv(f"{OUT}/real_loss_split.csv", index=False)
    print(pf.round(4).to_string(index=False)); print(pd.DataFrame(splits).round(1).to_string(index=False))
    print("R_lin 겉보기 활성화 에너지 [kJ/mol]: %.1f" % ea)
