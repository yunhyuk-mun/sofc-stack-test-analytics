"""측정 불확도를 반영한 항목별 판정. 항목마다 PASS / RETEST / FAIL을 먼저 정하고 합친다.
합치는 순서: 확정 FAIL이 하나라도 있으면 FAIL, 아니면 RETEST가 하나라도 있으면 RETEST, 아니면 PASS.
불확도를 적용하지 않는 항목(열화율)은 하한·상한을 그대로 쓴다."""
import math
from analyze import SPEC

PASS, RETEST, FAIL = "PASS", "RETEST", "FAIL"

def zone_lower(x, limit, U):
    """x가 limit 이상이어야 합격인 항목."""
    if x - U >= limit: return PASS
    if x + U < limit: return FAIL
    return RETEST

def zone_upper(x, limit, U):
    """x가 limit 이하여야 합격인 항목."""
    if x + U <= limit: return PASS
    if x - U > limit: return FAIL
    return RETEST

def item_zones(row, U, spec=SPEC):
    """row: mean_V, min_cell_V, spread, deg_pct_kh, worst_deg_pct_kh. U: 전압 확장 불확도 [V]."""
    return {
        "mean": zone_lower(row["mean_V"], spec["mean_V_min"], U),
        "cell": zone_lower(row["min_cell_V"], spec["cell_V_min"], U),
        # 셀간 편차는 두 셀 평균의 차이라 불확도를 sqrt(2)배로 적용한다.
        "spread": zone_upper(row["spread"], spec["spread_max"], U * math.sqrt(2)),
        "deg": PASS if row["deg_pct_kh"] <= spec["deg_max_pct_kh"] else FAIL,
        "worst": PASS if row["worst_deg_pct_kh"] <= spec["worst_cell_deg_max"] else FAIL,
    }

def final_verdict(row, U, spec=SPEC):
    z = item_zones(row, U, spec)
    vals = list(z.values())
    if FAIL in vals: return FAIL, z
    if RETEST in vals: return RETEST, z
    return PASS, z
