import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from judgement import final_verdict, zone_lower, zone_upper, PASS, RETEST, FAIL

U = 0.00206
OK = dict(mean_V=0.85, min_cell_V=0.82, spread=0.02, deg_pct_kh=0.5, worst_deg_pct_kh=0.8)

class JudgementTest(unittest.TestCase):
    def row(self, **kw):
        r = dict(OK); r.update(kw); return r

    def test_all_pass(self):
        self.assertEqual(final_verdict(OK, U)[0], PASS)

    def test_mean_just_below_limit_is_retest_not_fail(self):
        # 회귀 사례: 평균 전압만 하한 0.820 V보다 0.001 V 낮고 나머지는 통과
        v, z = final_verdict(self.row(mean_V=0.819), U)
        self.assertEqual(z["mean"], RETEST); self.assertEqual(v, RETEST)

    def test_mean_clearly_below_is_fail(self):
        self.assertEqual(final_verdict(self.row(mean_V=0.80), U)[0], FAIL)

    def test_confirmed_fail_dominates_retest(self):
        v, _ = final_verdict(self.row(mean_V=0.819, deg_pct_kh=2.0), U)
        self.assertEqual(v, FAIL)

    def test_boundaries_lower(self):
        self.assertEqual(zone_lower(0.82 + U, 0.82, U), PASS)
        self.assertEqual(zone_lower(0.82 - U, 0.82, U), RETEST)
        self.assertEqual(zone_lower(0.82 - U - 1e-6, 0.82, U), FAIL)

    def test_boundaries_upper(self):
        self.assertEqual(zone_upper(0.04 - U, 0.04, U), PASS)
        self.assertEqual(zone_upper(0.04 + U, 0.04, U), RETEST)
        self.assertEqual(zone_upper(0.04 + U + 1e-6, 0.04, U), FAIL)

    def test_spread_retest(self):
        self.assertEqual(final_verdict(self.row(spread=0.041), U)[0], RETEST)

if __name__ == "__main__":
    unittest.main()
