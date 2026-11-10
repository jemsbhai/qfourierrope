"""Overlap distribution of qfourierrope spectral fingerprints (exact).

Classical exact overlaps (no shot noise) over:
  - a substitution ladder on several base records (near-duplicate profile),
  - independent random record pairs (the false-equal risk class),
  - chemistry-style byte records (the qhashrope failure pair and relatives).

Question: where do identical, near-duplicate, and distinct records sit,
and is there a threshold that separates them? qhashrope's profile is
exact 1 / exact 0 by construction; this measures qfourierrope's.
"""

import json

import numpy as np

from qfourierrope.spectral import classical_overlap, spectral_angles

rng = np.random.default_rng(20261110)
BASES = [bytes(rng.choice(list(b"ACGT"), size=192)) for _ in range(6)]
LADDER = [0, 1, 2, 3, 5, 10, 20, 40]
CHEM = {
    "benzene": b"c1ccccc1",
    "cyclohexane": b"C1CCCCC1",
    "toluene": b"Cc1ccccc1",
    "pyridine": b"c1ccncc1",
}


def substitute(record: bytes, k: int, rng: np.random.Generator) -> bytes:
    if k == 0:
        return record
    b = bytearray(record)
    pos = rng.choice(len(b), size=min(k, len(b)), replace=False)
    for i in pos:
        choices = [c for c in b"ACGT" if c != b[i]]
        b[i] = choices[rng.integers(len(choices))]
    return bytes(b)


def stats(vals: list[float]) -> dict:
    v = np.array(vals)
    return {"n": len(v), "min": float(v.min()), "max": float(v.max()),
            "mean": float(v.mean()), "median": float(np.median(v))}


def main() -> None:
    out: dict = {}
    ladder: dict[str, list[float]] = {str(k): [] for k in LADDER}
    for base in BASES:
        ang = spectral_angles(base)
        for k in LADDER:
            var = substitute(base, k, rng)
            ladder[str(k)].append(classical_overlap(ang, spectral_angles(var)))
    out["substitution_ladder"] = {k: stats(v) for k, v in ladder.items()}

    indep = []
    for _ in range(200):
        a = bytes(rng.choice(list(b"ACGT"), size=192))
        b = bytes(rng.choice(list(b"ACGT"), size=192))
        indep.append(classical_overlap(spectral_angles(a), spectral_angles(b)))
    out["independent_pairs"] = stats(indep)

    chem_pairs = {}
    names = list(CHEM)
    for i, n1 in enumerate(names):
        for n2 in names[i + 1:]:
            chem_pairs[f"{n1} vs {n2}"] = classical_overlap(
                spectral_angles(CHEM[n1]), spectral_angles(CHEM[n2]))
    out["chemistry_pairs"] = chem_pairs

    distinct = indep + list(chem_pairs.values())
    near1 = ladder["1"]
    print("Substitution ladder (exact overlap vs base record):")
    for k in LADDER:
        s = out["substitution_ladder"][str(k)]
        print(f"  k={k:3d}  min={s['min']:.4f}  median={s['median']:.4f}  max={s['max']:.4f}")
    s = out["independent_pairs"]
    print(f"Independent pairs (n=200): min={s['min']:.4f} median={s['median']:.4f} max={s['max']:.4f}")
    print("Chemistry pairs:", {k: round(v, 4) for k, v in chem_pairs.items()})
    print("Threshold scan (false-equal on distinct, false-differ on 1-substitution):")
    for tau in [0.5, 0.6, 0.7, 0.8, 0.9, 0.95]:
        fe = float(np.mean([o >= tau for o in distinct]))
        fd = float(np.mean([o < tau for o in near1]))
        print(f"  tau={tau:.2f}  false-equal={fe:.3f}  false-differ(1-sub)={fd:.3f}")
    out["threshold_scan"] = {
        str(tau): {
            "false_equal_distinct": float(np.mean([o >= tau for o in distinct])),
            "false_differ_1sub": float(np.mean([o < tau for o in near1])),
        }
        for tau in [0.5, 0.6, 0.7, 0.8, 0.9, 0.95]
    }
    with open("distribution_results.json", "w") as f:
        json.dump(out, f, indent=2)
    print("wrote distribution_results.json")


if __name__ == "__main__":
    main()
