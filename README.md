# qfourierrope

**Spectral phase fingerprints for quantum equality testing.** Two parties hold a record and want one bit, identical or not, without moving the records: each side fingerprints its record locally and only the fingerprint travels. qfourierrope fingerprints a record by the phases of its block-hash spectrum and compares two fingerprints with a SWAP test. It is a spin-off of [qhashrope](https://github.com/jemsbhai/qhashrope) that takes the phase-fingerprint route qhashrope's README identifies as the path to a quantum communication advantage, and measures whether it works. Built by Muntaser Syed for the UCF edition of Qiskit Fall Fest 2026.

## Headline results (all measured 2026-11-10; raw data in the repo)

**Simulation, prototype pairs (Aer, 4096 shots; `run_prototype.py`):**

| Pair | Measured overlap | Exact overlap |
|---|---|---|
| DNA, identical | 1.0000 | 1.0000 |
| DNA, 1 substitution | 0.7207 | 0.7084 |
| DNA, 10 substitutions | 0.0073 | 0.0129 |
| Benzene vs cyclohexane | 0.0063 | 0.0000 |

**Distribution (exact overlaps; `EXPERIMENTS.md`, `distribution_results.json`):** independent 192-byte records never exceeded 0.0303 in 200 pairs, so exact-equality separation on long records is wide. But the overlap is not a similarity measure: it is non-monotonic in edit count (median 0.4769 at 1 substitution, 0.8137 at 2), and short records can collide: benzene vs pyridine, two distinct molecules, measure 0.9230.

**Noise (Aer, depolarizing p = 0.02; `noise_results.json`):** the identical pair contracts to 0.6123 in the monolithic 25-qubit circuit and to 0.4191 in the per-coefficient decomposed form. Decomposition makes it worse: each small circuit contributes a contraction factor of about 0.93 and the product compounds them (0.93^12 is about 0.42). qhashrope's decomposition works because it recombines decisions under an error-correcting code; this fingerprint has no code, so it has no decision level to recombine at.

**Hardware (ibm_fez, 2026-11-10; `HARDWARE.md`, `hardware_results.json`):**

| Pair | Exact | Monolithic, hardware | Decomposed, hardware |
|---|---|---|---|
| DNA identical | 1.0000 | 0.3506 | 0.2287 |
| DNA 1 substitution | 0.7084 | 0.2690 | 0.1501 |
| DNA 10 substitutions | 0.0129 | 0.0122 | not run |
| Benzene vs cyclohexane | 0.0000 | 0.0000 | not run |

The device confirms the simulation story: distinct pairs sit at the floor, the identical pair contracts harder than the p = 0.02 model predicts, and the decomposed form is again worse than the monolithic form, with per-coefficient P(0) uniformly 0.932 to 0.949 showing the same compounding mechanism. No threshold is claimed anywhere in this repo.

**Two-silo dedup at population scale (2026-11-11; `exp_dedup.py`, `dedup_results.json`, framing in `ADVANTAGE.md`):** two silos of 2,000 records each (192-byte slices of the E. coli K-12 reference genome), 200 records planted in both, all 4,000,000 cross pairs scored. Every planted duplicate recovered at overlap exactly 1.0000; zero false equals; the closest distinct pair in all 4M pairs reaches 0.7555 exact (a near-repeat region of the genome) and measures 0.7686 through the actual SWAP-test circuit, against duplicates measuring exactly 1.0000. `gpu_validate.py` extends the circuit-level check to the full duplicate population on a GPU (cuStateVec via qiskit-aer-gpu).

## The idea

qhashrope's fingerprint is a Golay (24,12,8)-expanded 12-bit message prepared as a basis state, which makes the decision exact at a single pre-set threshold, but a basis state carries no phase information, so the construction has no quantum communication advantage.

qfourierrope takes the phase route. The record is split into blocks and hashed with position-seeded hashes (the hashrope discipline). The block-hash sequence is treated as a discrete signal, and the fingerprint is the spectrum of that signal: the phases of the first 12 non-DC DFT coefficients, one per qubit, prepared as (|0> + e^{iθ} |1>) / √2. Two fingerprints are compared with a SWAP test, whose overlap factorises over the spectral coefficients as Π cos²(Δθⱼ / 2): exactly 1 for identical records, strictly below 1 when the block spectra differ.

## What is different, stated plainly

- qhashrope: error-corrected, exact, threshold fixed by construction (0.75), no quantum advantage yet.
- qfourierrope: phase-carrying, not error-corrected, no guaranteed minimum distance. Whether spectral phase differences separate identical from distinct records at a defensible threshold, and what the false-equal rate is, is an open empirical question. This repo exists to measure it; the scripts print raw overlaps with no threshold applied and no accuracy claimed.

Two honest observations from the measurements: benzene vs cyclohexane, the pair whose fingerprints collided under qhashrope's original encoding, separates cleanly here (0.0000 on hardware); and a single substitution already moves the overlap to about 0.71, because one changed block changes the whole spectrum. Near-duplicate sensitivity is therefore the hard case for this fingerprint, the opposite profile from a locality-preserving hash. Finding a phase fingerprint code with a cheap preparation circuit is the open problem both projects now point at.

## Run it

Environment: Python 3.12, Qiskit 2.6.2, Aer 0.18.2 (see `requirements.txt`).

```bash
pip install -r requirements.txt
python tests/test_spectral.py   # 2 tests for the fingerprint construction; prints "2 passed"
python run_prototype.py         # the four prototype pairs, measured vs exact
python exp_distribution.py      # Study 1: overlap distribution -> distribution_results.json
python exp_noise.py             # Study 2: noise, monolithic vs decomposed -> noise_results.json
```

Hardware scripts require an IBM Quantum account (run on instance "qhashrope", Open plan):

```bash
python submit_hardware.py       # submits to ibm_fez -> hardware_jobs.json
python retrieve_hardware.py     # harvests results -> hardware_results.json
```

## Hardware details

First run 2026-11-10 on **ibm_fez** (156-qubit Heron r2), SamplerV2, 4,096 shots per circuit. Two jobs: the monolithic 25-qubit SWAP test for the four study pairs (job `dbpk4i5t7fqc7389j2tg`), and the decomposed per-coefficient form, 12 independent 3-qubit SWAP tests per pair, for the identical and 1-substitution pairs (job `dbpk4i8ou4as73ctqohg`). Estimators match the simulation study: max(0, 2*P(0) - 1) for the monolithic circuit, and the product of the per-coefficient estimates for the decomposed form. Full reading in `HARDWARE.md`.

## Status

Hackathon prototype (v0.1.0). Spectral fingerprint, classical overlap reference, and SWAP-test circuits (monolithic and per-coefficient) implemented and unit-tested; distribution and noise studies complete; first hardware run done; Study 3 (two-silo dedup, 4M pairs, real genome) complete 2026-11-11. Next: GPU validation of the full duplicate population, more coefficients, magnitude-aware features, and the phase-code question.

## Layout

- `qfourierrope/spectral.py`: block signal, DFT, fingerprint angles, classical overlap.
- `qfourierrope/quantum_verify.py`: fingerprint preparation and SWAP test (Qiskit / Aer).
- `qfourierrope/qnoise.py`: depolarizing noise model used by the studies.
- `run_prototype.py`: identical vs distinct record overlaps, measured and exact.
- `exp_distribution.py`, `exp_noise.py`: the two studies in `EXPERIMENTS.md`; outputs in `distribution_results.json`, `noise_results.json`.
- `submit_hardware.py`, `retrieve_hardware.py`: the ibm_fez run; outputs in `hardware_jobs.json`, `hardware_results.json`.
- `exp_dedup.py`, `circuit_hardest.py`: Study 3, the two-silo dedup run; output in `dedup_results.json`; corpus `ecoli_k12.fna.gz` (NCBI RefSeq GCF_000005845.2, downloaded by the script if absent).
- `ADVANTAGE.md`: the quantum fingerprinting advantage claim, stated exactly, with its model and its limits.
- `gpu_validate.py`: circuit-level validation of the full duplicate population on GPU (qiskit-aer-gpu / cuStateVec); output in `gpu_validation_results.json`.
- `tests/`: unit tests for the fingerprint construction.

## License

MIT. The classical components derive from the author's published packages hashrope and multispecqr, used unmodified in qhashrope.
