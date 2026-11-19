"""Zenodo 5763484 (CC BY 4.0, Del Zotto et al.) 의 분극 곡선 시트를 CSV로 추출.
시트 BC_SP_02_IV_H2_std_{700,750,800}C: H2 50%/N2 50%, 공기 250 ml/min, 단전지(활성면적 3.5 cm2로 환산됨).
"""
import os, openpyxl, pandas as pd
HERE = os.path.dirname(__file__)
SRC = os.path.join(HERE, "..", "data", "zenodo_5763484", "DATA2.xlsx")
OUT = os.path.join(HERE, "..", "out")

def load():
    wb = openpyxl.load_workbook(SRC, data_only=True, read_only=True)
    rows = []
    for T in (700, 750, 800):
        ws = wb[f"BC_SP_02_IV_H2_std_{T}C"]
        for i, r in enumerate(ws.iter_rows(values_only=True)):
            if i < 8 or r[0] is None or r[3] is None:
                continue
            rows.append((T, float(r[0]), float(r[1]), float(r[3]), r[7]))
    return pd.DataFrame(rows, columns=["T_C", "j_A_cm2", "I_A", "V", "ASR_meas"])

if __name__ == "__main__":
    d = load()
    d.to_csv(os.path.join(OUT, "real_iv_curves.csv"), index=False)
    print(d.groupby("T_C").agg(n=("V", "size"), jmax=("j_A_cm2", "max"), ocv=("V", "max"), vmin=("V", "min")))
    print(d[d.j_A_cm2 == 0])
