"""Circuit-check the true hardest distinct pairs from Study 3.

Rebuilds the Study 3 silos and exact-overlap matrix with the same seed
(deterministic), finds the distinct cross pairs with the highest exact
overlaps, runs those pairs through the actual SWAP-test circuit on Aer
(4096 shots), and patches dedup_results.json: the distinct_hardest rows
are replaced with these true-hardest measurements.

Why this exists: the first Study 3 run selected its "hardest" pairs
with a masked-array indexing error, so its distinct circuit rows were
arbitrary distinct pairs rather than the closest ones. The exact
matrix results were unaffected. This script produces the circuit rows
the study actually intends.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from exp_dedup import N_A, N_B, N_DUP, RECORD_LEN, SEED, load_genome, overlap_matrix, sample_records
from qfourierrope import spectral_angles
from qfourierrope.quantum_verify import estimate_overlap

TOP = 12
RESULTS = Path(__file__).with_name("dedup_results.json")


def main() -> None:
    genome = load_genome()
    rng = np.random.default_rng(SEED)
    silo_a = sample_records(genome, N_A, RECORD_LEN, rng)
    dup_idx = rng.choice(N_A, size=N_DUP, replace=False)
    fresh_b = sample_records(genome, N_B - N_DUP, RECORD_LEN, rng)
    silo_b = [silo_a[i] for i in dup_idx] + fresh_b
    rng.shuffle(silo_b)
    planted = {(int(a), silo_b.index(silo_a[a])) for a in dup_idx}

    angles_a = np.array([spectral_angles(r) for r in silo_a])
    angles_b = np.array([spectral_angles(r) for r in silo_b])
    ov = overlap_matrix(angles_a, angles_b)
    is_dup = np.zeros_like(ov, dtype=bool)
    for a, b in planted:
        is_dup[a, b] = True

    masked = np.where(is_dup, -1.0, ov)
    hardest_flat = np.argsort(masked.ravel())[::-1][:TOP]
    hardest = np.array(np.unravel_index(hardest_flat, ov.shape)).T

    rows = []
    for a, b in hardest:
        r = estimate_overlap(silo_a[int(a)], silo_b[int(b)])
        rows.append({"kind": "distinct_hardest", "exact": r["exact_overlap"], "measured": r["measured_overlap"]})
        print(f"pair ({a}, {b}): exact={r['exact_overlap']:.4f} measured={r['measured_overlap']:.4f}", flush=True)

    results = json.loads(RESULTS.read_text())
    kept = [r for r in results["circuit_check_aer_4096_shots"] if r["kind"] != "distinct_hardest"]
    results["circuit_check_aer_4096_shots"] = kept + rows
    results["circuit_check_note"] = (
        "distinct_hardest rows are the 12 highest-overlap distinct pairs in the full "
        "4,000,000-pair matrix (patched in by circuit_hardest.py after an indexing "
        "fix in exp_dedup.py); duplicate rows are 12 of the 200 planted duplicates."
    )
    RESULTS.write_text(json.dumps(results, indent=2))
    print("patched", RESULTS)


if __name__ == "__main__":
    main()
