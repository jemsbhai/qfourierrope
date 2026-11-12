"""GPU validation of the full quantum pipeline at population scale.

Study 3 (exp_dedup.py) scores all 4,000,000 cross-silo pairs by the
exact overlap formula and checks only a small sample through the actual
SWAP-test circuit, because one 25-qubit circuit run costs seconds of
CPU time. This script closes that gap on a GPU: it runs the real
circuit (state preparation plus SWAP test, Aer statevector on
cuStateVec) for every planted duplicate and a large distinct-pair
sample, with and without the p = 0.02 depolarizing model, and reports
the referee's decision statistics from measured (shot) values only.

Requirements (Linux or WSL2; qiskit-aer-gpu has no native Windows
wheels): an NVIDIA GPU and
    pip install qiskit-aer-gpu
which pulls the cuQuantum runtime Aer uses. If no GPU backend is
available the script falls back to CPU and says so, and the timing
block then documents the CPU cost instead.

Run:
    python gpu_validate.py                # default workload
    python gpu_validate.py --distinct 2000 --noise-pairs 400

Outputs gpu_validation_results.json next to this file.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
from qiskit import transpile
from qiskit_aer import AerSimulator

from exp_dedup import N_A, N_B, N_DUP, RECORD_LEN, SEED, load_genome, overlap_matrix, sample_records
from qfourierrope import spectral_angles
from qfourierrope.qnoise import depolarizing
from qfourierrope.quantum_verify import swap_test_circuit

SHOTS = 4096


def make_simulator(noise_p: float) -> tuple[AerSimulator, str]:
    kwargs = {"method": "statevector", "seed_simulator": SEED}
    if noise_p > 0:
        kwargs["noise_model"] = depolarizing(noise_p)
    try:
        sim = AerSimulator(device="GPU", **kwargs)
        sim.run(transpile(swap_test_circuit(np.zeros(2), np.zeros(2)), sim), shots=8).result()
        return sim, "GPU (cuStateVec via qiskit-aer-gpu)"
    except Exception:
        return AerSimulator(**kwargs), "CPU fallback (GPU backend unavailable)"


def run_pairs(sim: AerSimulator, pairs, angles_a, angles_b, shots: int = SHOTS) -> list[float]:
    circuits = [transpile(swap_test_circuit(angles_a[a], angles_b[b]), sim) for a, b in pairs]
    counts = sim.run(circuits, shots=shots).result().get_counts()
    out = []
    for c in counts:
        p0 = c.get("0", 0) / shots
        out.append(max(0.0, 2.0 * p0 - 1.0))
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--distinct", type=int, default=500, help="random distinct pairs to validate")
    ap.add_argument("--noise-pairs", type=int, default=200, help="pairs re-run under p=0.02 noise")
    args = ap.parse_args()

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
    distinct_flat = np.dstack(np.unravel_index(np.argsort(ov[~is_dup].ravel())[::-1], ov.shape))[0]

    dup_pairs = sorted(planted)
    rng2 = np.random.default_rng(SEED + 1)
    rand_distinct = [(int(rng2.integers(N_A)), int(rng2.integers(N_B))) for _ in range(args.distinct)]
    rand_distinct = [(a, b) for a, b in rand_distinct if not is_dup[a, b]]
    hardest = [(int(a), int(b)) for a, b in distinct_flat[:100]]

    results: dict = {"shots": SHOTS, "workload": {"duplicates": len(dup_pairs), "distinct_random": len(rand_distinct), "distinct_hardest": len(hardest)}}

    for label, noise_p in [("noiseless", 0.0), ("depolarizing_p_0.02", 0.02)]:
        sim, device = make_simulator(noise_p)
        results.setdefault("backend", device)
        t0 = time.time()
        if label == "noiseless":
            work = [("duplicate", dup_pairs), ("distinct_random", rand_distinct), ("distinct_hardest", hardest)]
        else:
            work = [("duplicate", dup_pairs[: args.noise_pairs]), ("distinct_hardest", hardest[: args.noise_pairs])]
        block = {}
        for kind, pairs in work:
            measured = run_pairs(sim, pairs, angles_a, angles_b)
            exact = [float(ov[a, b]) for a, b in pairs]
            block[kind] = {
                "pairs": len(pairs),
                "measured_min": float(np.min(measured)) if kind == "duplicate" else None,
                "measured_max": float(np.max(measured)) if kind != "duplicate" else None,
                "mean_abs_error_vs_exact": float(np.mean(np.abs(np.array(measured) - np.array(exact)))),
            }
        block["seconds"] = round(time.time() - t0, 1)
        results[label] = block

    Path(__file__).with_name("gpu_validation_results.json").write_text(json.dumps(results, indent=2))
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
