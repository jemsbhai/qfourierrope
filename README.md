# qfourierrope

**Spectral phase fingerprints for quantum equality testing.** A spin-off of [qhashrope](https://github.com/jemsbhai/qhashrope), built for the DeepStation edition of Qiskit Fall Fest 2026.

## The idea

qhashrope decides whether two large records are identical without moving the records: each side fingerprints its record locally and only the fingerprint travels. Its fingerprint is a Golay (24,12,8)-expanded 12-bit message prepared as a basis state, which makes the decision exact at a single pre-set threshold, but a basis state carries no phase information, so the construction has no quantum communication advantage. The qhashrope README names the fix directly: the phase fingerprint is the route to one.

qfourierrope takes that route. The record is split into blocks and hashed with position-seeded hashes (the hashrope discipline). The block-hash sequence is treated as a discrete signal, and the fingerprint is the spectrum of that signal: the phases of the first 12 non-DC DFT coefficients, one per qubit, prepared as (|0> + e^{iθ} |1>) / √2. Two fingerprints are compared with a SWAP test, whose overlap factorises over the spectral coefficients as Π cos²(Δθⱼ / 2): exactly 1 for identical records, strictly below 1 when the block spectra differ.

## What is different, stated plainly

- qhashrope: error-corrected, exact, threshold fixed by construction (0.75), no quantum advantage yet.
- qfourierrope: phase-carrying, not error-corrected, no guaranteed minimum distance. Whether spectral phase differences separate identical from distinct records at a defensible threshold, and what the false-equal rate is, is an open empirical question. This repo exists to measure it; `run_prototype.py` prints raw overlaps with no threshold applied and no accuracy claimed.

## First measurements (Aer simulation, 4096 shots, 2026-11-10)

| Pair | Measured overlap | Exact overlap |
|---|---|---|
| DNA, identical | 1.0000 | 1.0000 |
| DNA, 1 substitution | 0.7207 | 0.7084 |
| DNA, 10 substitutions | 0.0073 | 0.0129 |
| Benzene vs cyclohexane | 0.0063 | 0.0000 |

Four pairs only, no threshold claimed. Two honest observations: benzene vs cyclohexane, the pair whose fingerprints collided under qhashrope's original encoding, separates cleanly here; and a single substitution already moves the overlap to about 0.71, because one changed block changes the whole spectrum. Near-duplicate sensitivity is therefore the hard case for this fingerprint, the opposite profile from a locality-preserving hash.

## Experiment results (2026-11-10, see EXPERIMENTS.md)

- **Distribution (exact overlaps):** independent 192-byte records never exceeded 0.0303 in 200 pairs, so exact-equality separation on long records is wide. But the overlap is not a similarity measure: it is non-monotonic in edit count (median 0.48 at 1 substitution, 0.81 at 2), and short records can collide: benzene vs pyridine, two distinct molecules, measure 0.9230.
- **Noise (Aer, depolarizing p = 0.02):** the identical pair contracts to 0.6123 in the monolithic circuit and to 0.4191 in the per-coefficient decomposed form. Decomposition makes it worse, because each small circuit's contraction compounds in the product (about 0.93^12), the same failure as qhashrope's analog product recombination. qhashrope's decomposition works because it recombines decisions under an error-correcting code; this fingerprint has no code, so it has no decision level to recombine at. Finding a phase fingerprint code with a cheap preparation circuit is the open problem both projects now point at.

## Status

Hackathon prototype (v0.1.0). Spectral fingerprint, classical overlap reference, and SWAP-test circuits (monolithic and per-coefficient) implemented and unit-tested; distribution and noise studies complete as above. Next: record-length scaling of the collision rate, more coefficients, magnitude-aware features.

## Layout

- `qfourierrope/spectral.py`: block signal, DFT, fingerprint angles, classical overlap.
- `qfourierrope/quantum_verify.py`: fingerprint preparation and SWAP test (Qiskit / Aer).
- `run_prototype.py`: identical vs distinct record overlaps, measured and exact.
- `tests/`: unit tests for the fingerprint construction.

## License

MIT. The classical components derive from the author's published packages hashrope and multispecqr, used unmodified in qhashrope.
