"""전체 파이프라인을 순서대로 실행하고 테스트까지 돌린다.  사용: python -I run_all.py
(필요 패키지: pip install -r requirements.txt)"""
import os, subprocess, sys
ROOT = os.path.dirname(os.path.abspath(__file__))
STEPS = ["run_all", "seed_sweep", "analyze_real", "degradation", "sensitivity", "rig_stats",
         "noise_sweep", "guard_band", "report", "decision_table"]
for s in STEPS:
    print(f"[실행] src/{s}.py", flush=True)
    subprocess.run([sys.executable, "-I", os.path.join(ROOT, "src", f"{s}.py")], check=True, cwd=ROOT)
print("[테스트]", flush=True)
subprocess.run([sys.executable, "-I", "-m", "unittest", "discover", "-s", "tests", "-v"], check=True, cwd=ROOT)
print("완료: 결과는 out/ 에 저장되었습니다.")
