"""스택 평가 데이터 분석: 합·부 판정, 열화율, 셀 이상 탐지, 호기 편차, 원인 분류.

판정 기준(SPEC)은 이 프로젝트에서 임의로 둔 가정값이다. 실제 양산 기준이 아니다.
"""
from __future__ import annotations
import numpy as np
import pandas as pd

SPEC = {
    "mean_V_min": 0.82,       # 초기(0~50h) 셀 평균 전압 하한 [V]
    "cell_V_min": 0.78,       # 초기 최저 셀 전압 하한 [V]
    "deg_max_pct_kh": 1.5,    # 열화율 상한 [%/1000h]
    "worst_cell_deg_max": 3.0,  # 최악 셀 열화율 상한 [%/1000h]
    "spread_max": 0.040,      # 초기 셀간 전압 편차(max-min) 상한 [V]
}


def stack_features(df: pd.DataFrame) -> pd.DataFrame:
    early = df[df.hour <= 50]
    out = []
    for sid, g in df.groupby("stack"):
        e = early[early["stack"] == sid]
        cm = e.groupby("cell").cell_V.mean()
        # 열화율: 스택 평균 전압의 시간 선형회귀 기울기 / 초기 전압
        m = g.groupby("hour").cell_V.mean()
        slope = np.polyfit(m.index.values, m.values, 1)[0]
        deg = -slope * 1000 / m.iloc[0] * 100
        # 셀별 열화율 -> 최악 셀
        worst_deg, worst_cell = -1e9, 0
        for c, gc in g.groupby("cell"):
            mc = gc.sort_values("hour").cell_V
            sl = np.polyfit(gc.sort_values("hour").hour.values, mc.values, 1)[0]
            d = -sl * 1000 / mc.iloc[0] * 100
            if d > worst_deg:
                worst_deg, worst_cell = d, int(c)
        out.append({
            "stack": sid, "rig": g.rig.iloc[0],
            "mean_V": cm.mean(), "min_cell_V": cm.min(), "min_cell": int(cm.idxmin()),
            "spread": cm.max() - cm.min(),
            "deg_pct_kh": deg, "worst_deg_cell": worst_cell, "worst_deg_pct_kh": worst_deg,
            "temp_K": e.temp_K.mean(),
        })
    return pd.DataFrame(out)


def judge(f: pd.DataFrame, spec=SPEC) -> pd.DataFrame:
    f = f.copy()
    f["pass_mean"] = f.mean_V >= spec["mean_V_min"]
    f["pass_cell"] = f.min_cell_V >= spec["cell_V_min"]
    f["pass_deg"] = f.deg_pct_kh <= spec["deg_max_pct_kh"]
    f["pass_spread"] = f.spread <= spec["spread_max"]
    f["pass_worst"] = f.worst_deg_pct_kh <= spec["worst_cell_deg_max"]
    f["verdict"] = np.where(f[["pass_mean", "pass_cell", "pass_deg", "pass_spread", "pass_worst"]].all(axis=1), "PASS", "FAIL")
    return f


def classify(f: pd.DataFrame, spec=SPEC) -> pd.DataFrame:
    """합·부 판정이 FAIL인 스택의 원인을 규칙으로 분류한다.

    - 한 셀만 낮다(스프레드 큼, 평균은 정상)      -> gas_leak (단일 셀 누설/조립 불량)
    - 평균은 정상인데 한 셀 열화가 큼              -> contact_degradation
    - 평균이 전체적으로 낮다                       -> low_performance
    - 호기 R3 소속이면서 평균 편차가 호기 효과 범위  -> rig_suspect (설비 점검 후 재평가)
    """
    f = f.copy()
    rig_mean = f.groupby("rig").mean_V.median()
    ref = rig_mean.drop(index=rig_mean.idxmin()).mean()
    f["rig_offset"] = f.rig.map(rig_mean) - ref
    cause = []
    for _, r in f.iterrows():
        if r.verdict == "PASS":
            cause.append("none")
        elif r.worst_deg_pct_kh > 3.0 and r.spread <= spec["spread_max"] * 2:
            cause.append("contact_degradation")
        elif r.mean_V < spec["mean_V_min"] and r.spread <= spec["spread_max"]:
            cause.append("rig_suspect" if r.rig_offset < -0.003 else "low_performance")
        elif r.spread > spec["spread_max"]:
            cause.append("gas_leak")
        else:
            cause.append("low_performance")
    f["cause"] = cause
    return f


# 분류 코드별 "관측"(데이터에서 본 것)과 "가설"(그 관측을 만드는 후보 원인). 가설은 점검 대상일 뿐 진단이 아니다.
OBS_HYP = {
    "gas_leak": ("단일 셀 저전압, 셀간 편차가 기준 초과", "가스 누설·시일 불량 등 점검 필요 (접촉 불량이나 셀 불량도 같은 패턴을 낼 수 있음)"),
    "contact_degradation": ("한 셀의 열화율이 다른 셀보다 크게 높음", "접촉 저항 증가·체결 상태 등 점검 필요"),
    "low_performance": ("스택 전체 평균 전압이 기준 미만", "제조 산포·연료 조건·계측 오차 등 점검 필요"),
    "rig_suspect": ("평균 전압이 낮고 같은 호기 스택이 함께 낮음", "호기 온도·계측 정합성 점검 필요 (스택 결함으로 단정하지 않음)"),
    "none": ("기준 이내", "-"),
}
