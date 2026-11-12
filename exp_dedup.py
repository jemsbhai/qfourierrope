"""Study 3: two-silo record matching with quantum fingerprints only.

Scenario (see ADVANTAGE.md): two institutions each hold genomic records.
They want the set of records they share. The records never move: each side
computes the 12-qubit spectral phase fingerprint of each of its records
locally, only the fingerprints go to a referee, and the referee runs SWAP
tests. Identical records give overlap exactly 1 by construction; the
empirical question is the separation to the closest distinct pair.

Corpus: records are contiguous slices of the public Escherichia coli
K-12 MG1655 reference genome (NC_000913.3, 4,641,652 bases, NCBI RefSeq
GCF_000005845.2), used as public stand-in record material. The protocol
is record-agnostic; nothing about the construction is specific to DNA.

Silo A: N_A records sampled at seeded random offsets.
Silo B: N_B records, of which N_DUP are exact copies of seeded Silo A
records (the planted shared set) and the rest are fresh slices.
All cross-silo pairs are scored by exact overlap from the angles; a
sample of pairs (planted duplicates and the hardest distinct pairs) is
also run through the actual SWAP-test circuit on Aer.

Outputs dedup_results.json. No threshold is imposed by the code beyond
the reporting cut in the summary: identical is overlap 1, and the study
reports the largest distinct-pair overlap actually observed, so the
margin is a measured quantity, not an assumption.
"""

from __future__ import annotations

import gzip
import json
import time
import urllib.request
from pathlib import Path

import numpy as np

from qfourierrope import classical_overlap, spectral_angles
from qfourierrope.quantum_verify import estimate_overlap

GENOME_URL = (
    "https://ftp.ncbi.nlm.nih.gov/genomes/all/GCF/000/005/845/"
    "GCF_000005845.2_ASM584v2/GCF_000005845.2_ASM584v2_genomic.fna.gz"
)
GENOME_PATH = Path(__file__).with_name("ecoli_k12.fna.gz")

SEED = 20261111
RECORD_LEN = 192  # bytes per record, the repo's standing record size
N_A = 2000
N_B = 2000
N_DUP = 200
SWEEP_LENS = [64, 192, 1024, 4096]
SWEEP_PAIRS = 500
CIRCUIT_SAMPLE_DUP = 12
CIRCUIT_SAMPLE_DISTINCT = 12


def load_genome() -> bytes:
    if not GENOME_PATH.exists():
        urllib.request.urlretrieve(GENOME_URL, GENOME_PATH)
    with gzip.open(GENOME_PATH, "rt") as fh:
        seq = "".join(line.strip() for line in fh if not line.startswith(">"))
    return seq.encode("ascii")


def sample_records(genome: bytes, n: int, length: int, rng: np.random.Generator,
                   exclude_starts: set[int] | None = None) -> list[bytes]:
    starts: set[int] = set(exclude_starts or set())
    out: list[bytes] = []
    max_start = len(genome) - length
    while len(out) < n:
        s = int(rng.integers(0, max_start))
        if s in starts:
            continue
        starts.add(s)
        out.append(genome[s : s + length])
    return out


def overlap_matrix(angles_a: np.ndarray, angles_b: np.ndarray) -> np.ndarray:
    """Exact overlaps for all cross pairs, chunked over rows of A."""
    out = np.empty((len(angles_a), len(angles_b)), dtype=np.float64)
    for i in range(0, len(angles_a), 250):
        block = angles_a[i : i + 250]
        d = (block[:, None, :] - angles_b[None, :, :]) / 2.0
        out[i : i + 250] = np.prod(np.cos(d) ** 2, axis=2)
    return out


def main() -> None:
    t0 = time.time()
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

    dup_overlaps = ov[is_dup]
    distinct_overlaps = ov[~is_dup]
    recovered = int(np.sum(dup_overlaps > 0.999999))
    false_equals = int(np.sum(distinct_overlaps > 0.999999))
    max_distinct = float(distinct_overlaps.max())
    masked = np.where(is_dup, -1.0, ov)
    hardest_flat = np.argsort(masked.ravel())[::-1][:CIRCUIT_SAMPLE_DISTINCT]
    hardest = np.array(np.unravel_index(hardest_flat, ov.shape)).T

    # Circuit-level check: planted duplicates and hardest distinct pairs.
    circuit_rows = []
    dup_pairs = sorted(planted)[:CIRCUIT_SAMPLE_DUP]
    for a, b in dup_pairs:
        r = estimate_overlap(silo_a[a], silo_b[b])
        circuit_rows.append({"kind": "duplicate", "exact": r["exact_overlap"], "measured": r["measured_overlap"]})
    for a, b in hardest:
        r = estimate_overlap(silo_a[int(a)], silo_b[int(b)])
        circuit_rows.append({"kind": "distinct_hardest", "exact": r["exact_overlap"], "measured": r["measured_overlap"]})

    # Length sweep: separation vs record length on fresh random pairs.
    sweep = {}
    for length in SWEEP_LENS:
        recs_a = sample_records(genome, SWEEP_PAIRS, length, rng)
        recs_b = sample_records(genome, SWEEP_PAIRS, length, rng)
        aa = np.array([spectral_angles(r) for r in recs_a])
        ab = np.array([spectral_angles(r) for r in recs_b])
        vals = np.array([classical_overlap(x, y) for x, y in zip(aa, ab)])
        sweep[str(length)] = {"pairs": SWEEP_PAIRS, "max_overlap": float(vals.max()), "median_overlap": float(np.median(vals))}

    results = {
        "study": "two-silo dedup, fingerprint-only matching",
        "corpus": "E. coli K-12 MG1655 (NC_000913.3), contiguous slices",
        "seed": SEED,
        "record_len_bytes": RECORD_LEN,
        "silo_sizes": {"A": N_A, "B": N_B},
        "planted_duplicates": N_DUP,
        "cross_pairs_scored": int(ov.size),
        "duplicates_recovered_at_overlap_gt_0.999999": recovered,
        "false_equals_at_overlap_gt_0.999999": false_equals,
        "duplicate_overlap_min": float(dup_overlaps.min()),
        "max_distinct_overlap": max_distinct,
        "circuit_check_aer_4096_shots": circuit_rows,
        "length_sweep_distinct_pairs": sweep,
        "runtime_seconds": round(time.time() - t0, 1),
    }
    Path(__file__).with_name("dedup_results.json").write_text(json.dumps(results, indent=2))
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
