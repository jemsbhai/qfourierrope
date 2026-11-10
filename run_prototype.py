"""qfourierrope prototype: SWAP-test overlaps for identical/distinct records.

Prints measured (Aer simulation, 4096 shots) and exact classical overlaps.
No threshold is applied and no accuracy is claimed: this run produces the
raw overlap distribution that a threshold would have to separate.
"""

from qfourierrope.quantum_verify import estimate_overlap

DNA_A = (b"ACGTGCAATGCCGTTAACGGATCCTAGGCAATCGGATCCATTAACCGG" * 4)
DNA_A_COPY = DNA_A
DNA_1SUB = DNA_A[:17] + b"T" + DNA_A[18:]
DNA_10SUB = bytearray(DNA_A)
for i in range(0, len(DNA_10SUB), 19):
    DNA_10SUB[i] = ord("T") if DNA_10SUB[i] != ord("T") else ord("A")
DNA_10SUB = bytes(DNA_10SUB)
BENZENE = b"c1ccccc1"
CYCLOHEXANE = b"C1CCCCC1"

PAIRS = [
    ("DNA identical", DNA_A, DNA_A_COPY, True),
    ("DNA 1 substitution", DNA_A, DNA_1SUB, False),
    ("DNA 10 substitutions", DNA_A, DNA_10SUB, False),
    ("benzene vs cyclohexane", BENZENE, CYCLOHEXANE, False),
]

if __name__ == "__main__":
    for name, a, b, _ in PAIRS:
        r = estimate_overlap(a, b)
        print(
            f"{name:26s} P(0)={r['p0']:.4f}  measured overlap={r['measured_overlap']:.4f}"
            f"  exact overlap={r['exact_overlap']:.4f}"
        )
