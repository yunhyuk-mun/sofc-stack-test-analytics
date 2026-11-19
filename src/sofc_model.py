"""SOFC 셀/스택 분극 모델 (단순 0차원 모델).

주의: 모든 파라미터는 공개 문헌 수준의 대표값으로 정한 가정값이며,
특정 기업의 실제 제품·시험 데이터가 아니다. 데이터는 전부 시뮬레이션이다.
"""
from __future__ import annotations
import numpy as np

F = 96485.0
R = 8.314


def nernst(T_K: float, pH2: float, pH2O: float, pO2: float = 0.21) -> float:
    e0 = 1.253 - 2.4516e-4 * T_K
    return e0 + (R * T_K / (2 * F)) * np.log(pH2 * np.sqrt(pO2) / pH2O)


def cell_voltage(i, T_K=973.0, fu=0.7, asr_ohm=0.12, i0=0.35, i_lim=1.6, alpha=0.5):
    """i: 전류밀도 [A/cm2]. fu: 연료이용률(0~1). asr_ohm: [ohm*cm2]."""
    i = np.asarray(i, dtype=float)
    # 입구 H2 : H2O = 0.97:0.03 가정, 이용률에 따른 평균 조성 근사
    h2 = 0.97 * (1 - fu / 2)
    h2o = 1 - h2
    e = nernst(T_K, h2, h2o)
    v_act = (R * T_K / (alpha * F)) * np.arcsinh(i / (2 * i0))
    v_ohm = asr_ohm * i
    v_conc = -(R * T_K / (2 * F)) * np.log(np.clip(1 - i / i_lim, 1e-3, None))
    return e - v_act - v_ohm - v_conc
