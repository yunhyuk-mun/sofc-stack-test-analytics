import os, sys, unittest
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from sofc_model import cell_voltage
from analyze_real import curvature_deviation, slope_ratio, CONC_FLAG_MV

J = np.arange(0.0286, 0.82, 0.0286)

class CurvatureTest(unittest.TestCase):
    def curve(self, i_lim, noise=0.0008, seed=0):
        rng = np.random.default_rng(seed)
        return np.asarray(cell_voltage(J, i_lim=i_lim)) + rng.normal(0, noise, len(J))

    def test_detects_strong_concentration_loss(self):
        for i_lim in (0.85, 0.9):                     # 끝점에서 농도 손실이 90 mV 안팎인 곡선(양성 사례)
            dev = curvature_deviation(J, self.curve(i_lim))
            self.assertLess(dev, -CONC_FLAG_MV, f"i_lim={i_lim} dev={dev:.1f} mV")

    def test_known_limit_moderate_loss_is_not_detected(self):
        # 알려진 한계: 끝점 농도 손실이 약 46 mV(i_lim=1.2)여도 이 방법은 -5 mV 기준을 넘지 못한다.
        dev = curvature_deviation(J, self.curve(1.2))
        self.assertGreater(dev, -CONC_FLAG_MV)

    def test_no_flag_without_concentration_loss(self):
        for seed in range(10):                        # 한계전류가 매우 큰 곡선(음성 사례)
            dev = curvature_deviation(J, self.curve(50.0, seed=seed))
            self.assertGreater(dev, -CONC_FLAG_MV, f"seed={seed} dev={dev:.1f} mV")

    def test_slope_ratio_separates_strong_loss(self):
        hi = slope_ratio(J, self.curve(1.0)); lo = slope_ratio(J, self.curve(50.0))
        self.assertGreater(hi, 1.05); self.assertLess(lo, 1.0)

    def test_short_curve_not_evaluated(self):
        j = J[J <= 0.45]
        self.assertTrue(np.isnan(curvature_deviation(j, np.asarray(cell_voltage(j)))))

if __name__ == "__main__":
    unittest.main()
