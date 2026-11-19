"""장기 운전 열화 분석: 열화율 산출과 정상 감소 / 급변 구간 구분.

입력: 시간 대 스택(또는 셀) 전압. 실측 장기 데이터는 확보하지 못해, 알려진 이벤트를 심은 시뮬레이션 2000 h 데이터로
방법을 검증한다. (Zenodo 5763484에는 140 h 안정성 시험 원자료가 없고 분극 곡선만 있다.)
판정 임계값은 모두 가정값이다.
"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams["font.family"] = "Malgun Gothic"; plt.rcParams["axes.unicode_minus"] = False
OUT = os.path.join(os.path.dirname(__file__), "..", "out")
WIN = 48                  # 비교/기울기 창 [h]
BASE_H = 500              # 기준 열화율을 구하는 초기 구간 [h]
STEP_MV = 6.0             # 급강하 판정 하한 [mV] (가정)
STEP_SIGMA = 5.0          # 노이즈 대비 배수
SLOPE_X = 3.0             # 기준 열화율 대비 가속 배수
SLOPE_MIN = 1.5           # 가속 판정 절대 하한 [%/kh]


def simulate(seed=7, hours=2000, v0=0.85, noise=0.0015, events=True):
    rng = np.random.default_rng(seed)
    t = np.arange(0, hours + 1, 1.0)
    rate = np.full_like(t, 0.5 / 1000 / 100)               # 0.5 %/kh
    if events:
        rate[t >= 1500] = 3.5 / 1000 / 100                  # 1500 h 이후 가속 열화 3.5 %/kh
    v = v0 * np.cumprod(1 - rate)
    if events:
        v[t >= 1100] -= 0.012                               # 1100 h 급강하 12 mV
    v += rng.normal(0, noise, len(t))
    return pd.DataFrame({"hour": t, "V": v})


def detect(df):
    t, v = df.hour.values, df.V.values
    base = df[df.hour <= BASE_H]
    slope0, c0 = np.polyfit(base.hour, base.V, 1)
    deg0 = -slope0 * 1000 / c0 * 100                        # %/kh
    sigma = np.std(base.V - (slope0 * base.hour + c0))
    # 급강하: 인접한 두 창의 평균 차이
    steps = []
    for i in range(WIN, len(t) - WIN):
        d = v[i:i + WIN].mean() - v[i - WIN:i].mean()
        expected = slope0 * WIN
        if d - expected < -max(STEP_MV / 1000, STEP_SIGMA * sigma * np.sqrt(2 / WIN) * 3):
            steps.append((t[i], (d - expected) * 1000))
    ev = []
    for hh, mv in steps:
        if not ev or hh - ev[-1]["hour"] > WIN:
            ev.append({"type": "step_drop", "hour": hh, "mV": mv})
        elif mv < ev[-1]["mV"]:
            ev[-1].update(hour=hh, mV=mv)
    # 가속: 급강하 주변을 제외한 롤링 기울기
    roll = np.full(len(t), np.nan)
    for i in range(WIN * 2, len(t) - WIN * 2):
        seg = slice(i - WIN * 2, i + WIN * 2)
        roll[i] = -np.polyfit(t[seg], v[seg], 1)[0] * 1000 / v[i] * 100
    for e in ev:
        roll[(t > e["hour"] - 2 * WIN) & (t < e["hour"] + 2 * WIN)] = np.nan
    acc = (roll > max(SLOPE_X * deg0, SLOPE_MIN))
    if acc.any():
        ev.append({"type": "accelerated_degradation", "hour": float(t[np.argmax(acc)]),
                   "mV": float(np.nanmax(roll[acc]))})
    return deg0, sigma, roll, ev


if __name__ == "__main__":
    df = simulate(); df.to_csv(f"{OUT}/sim_long_run.csv", index=False)
    deg0, sigma, roll, ev = detect(df)
    pd.DataFrame(ev).round(2).to_csv(f"{OUT}/degradation_events.csv", index=False)
    print("기준 열화율(초기 %d h): %.2f %%/kh, 노이즈 sigma %.2f mV" % (BASE_H, deg0, sigma * 1000))
    for e in ev: print(e)
    fig, ax = plt.subplots(2, 1, figsize=(7, 6), sharex=True)
    ax[0].plot(df.hour, df.V, lw=.7, color="gray")
    base = df[df.hour <= BASE_H]; s, c = np.polyfit(base.hour, base.V, 1)
    ax[0].plot(df.hour, s * df.hour + c, "g--", label="초기 기준 외삽")
    for e in ev:
        ax[0].axvline(e["hour"], color="r" if e["type"] == "step_drop" else "orange", ls=":")
    ax[0].set_ylabel("전압 [V]"); ax[0].set_title("장기 운전 전압과 이상 구간 (시뮬레이션)"); ax[0].legend()
    ax[1].plot(df.hour, roll, color="tab:blue"); ax[1].axhline(max(SLOPE_X * deg0, SLOPE_MIN), color="orange", ls="--", label="가속 판정선")
    ax[1].axhline(deg0, color="g", ls="--", label="기준 열화율"); ax[1].set_ylabel("롤링 열화율 [%/kh]"); ax[1].set_xlabel("시간 [h]"); ax[1].legend()
    fig.tight_layout(); fig.savefig(f"{OUT}/sim_degradation.png", dpi=140)
