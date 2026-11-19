"""양산 평가 라인 시뮬레이션 데이터 생성 (전부 가상 데이터).

호기(평가설비) 3대, 스택 60개, 스택당 N_CELL 셀.
각 스택은 평가 중 0.4 A/cm2 정전류 유지, 일정 간격으로 셀 전압을 기록.
주입한 결함(정답)은 analyze 단계에서 맞히는지 검증하는 용도로 별도 저장한다.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from sofc_model import cell_voltage

SEED = 42
N_STACK = 60
N_CELL = 30
HOURS = np.arange(0, 501, 25)        # 500 h, 25 h 간격
I_OP = 0.4                           # A/cm2
RIGS = ["R1", "R2", "R3"]


def make(seed: int = SEED):
    rng = np.random.default_rng(seed)
    rows, truth = [], []
    for s in range(N_STACK):
        rig = RIGS[s % 3]
        sid = f"S{s + 1:03d}"
        # 셀별 제조 산포
        asr = rng.normal(0.12, 0.008, N_CELL)
        i0 = rng.normal(0.35, 0.02, N_CELL)
        deg_rate = np.full(N_CELL, rng.normal(0.4, 0.1))   # %/kh 기본 열화
        fault = None
        cell_bad = -1
        r = rng.random()
        if r < 0.10:                       # 1) 한 셀 가스 누설(크로스리크) -> 전압 하락
            fault, cell_bad = "gas_leak", int(rng.integers(0, N_CELL))
            asr[cell_bad] += 0.10
        elif r < 0.18:                     # 2) 접촉 불량 -> 열화 가속
            fault, cell_bad = "contact_degradation", int(rng.integers(0, N_CELL))
            deg_rate[cell_bad] = rng.normal(6.0, 1.0)
        elif r < 0.24:                     # 3) 스택 전체 저성능 (Ink/소결 이슈 가정)
            fault = "low_performance"
            asr += 0.06
            i0 *= 0.8
        # 호기 R3의 온도 편차 (평가설비 이슈 가정): 계측 오프셋 -> 스택 결함 아님
        t_off = {"R1": 0.0, "R2": 0.0, "R3": -12.0}[rig]
        for h in HOURS:
            T_K = 973.0 + t_off + rng.normal(0, 1.0)
            for c in range(N_CELL):
                arr = np.exp(9000 * (1 / T_K - 1 / 973.0))   # 온도에 따른 저항 증가(아레니우스 근사)
                v0 = float(cell_voltage(I_OP, T_K=T_K, asr_ohm=asr[c] * arr, i0=i0[c] * arr ** -1))
                v = v0 * (1 - deg_rate[c] / 100 * h / 1000) + rng.normal(0, 0.002)
                rows.append((sid, rig, int(h), c + 1, round(T_K, 1), round(v, 4)))
        truth.append((sid, rig, fault or "none", cell_bad + 1 if cell_bad >= 0 else 0))
    df = pd.DataFrame(rows, columns=["stack", "rig", "hour", "cell", "temp_K", "cell_V"])
    gt = pd.DataFrame(truth, columns=["stack", "rig", "fault", "bad_cell"])
    return df, gt


if __name__ == "__main__":
    df, gt = make()
    df.to_csv("out/test_data.csv", index=False)
    gt.to_csv("out/ground_truth.csv", index=False)
    print(df.shape, gt.fault.value_counts().to_dict())
