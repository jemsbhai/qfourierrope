# qfourierrope experiments, 2026-11-10

Two studies, both run on the day the repo was created. Environment:
Python 3.12.3, Qiskit 2.6.2, Aer 0.18.2, MPS simulator, 4096 shots per
circuit where shots apply. Scripts: `exp_distribution.py`,
`exp_noise.py`; raw data: `distribution_results.json`,
`noise_results.json`.

## Study 1: overlap distribution (exact classical overlaps)

Question: where do identical, near-duplicate, and distinct records sit,
and can a threshold separate them? 6 base DNA-like records (192 bytes),
substitution ladder; 200 independent random pairs; 4 chemistry-style
byte records (SMILES strings).

Substitution ladder, exact overlap vs the base record (median over 6 bases):

| Substitutions | min | median | max |
|---|---|---|---|
| 0 | 1.0000 | 1.0000 | 1.0000 |
| 1 | 0.0001 | 0.4769 | 0.8950 |
| 2 | 0.2776 | 0.8137 | 0.9325 |
| 3 | 0.0000 | 0.2344 | 0.7727 |
| 5 | 0.0000 | 0.1300 | 0.3478 |
| 10 | 0.0000 | 0.0008 | 0.1112 |
| 20 | 0.0000 | 0.0002 | 0.0188 |
| 40 | 0.0000 | 0.0000 | 0.0000 |

Independent pairs (n=200): median 0.0000, max 0.0303.

Chemistry pairs: benzene vs cyclohexane 0.0000, benzene vs toluene
0.0000, cyclohexane vs toluene 0.0003, cyclohexane vs pyridine 0.0000,
toluene vs pyridine 0.0000, **benzene vs pyridine 0.9230**.

Findings:

1. **Distinct long records separate cleanly.** Independent 192-byte
   records never exceeded 0.0303 in 200 pairs. For exact-equality
   decisions on records of this size, the separation from identical
   (exactly 1.0000) is wide.
2. **The overlap is not a similarity measure.** It is non-monotonic in
   edit count (2 substitutions sit higher, median 0.81, than 1
   substitution, median 0.48) and high-variance at fixed edit count
   (1 substitution spans 0.0001 to 0.8950). One changed block scrambles
   the whole spectrum, so the magnitude says "changed", never "how
   much". This is the opposite profile from qhashrope's predecessor
   failure mode, and it rules out grading near-duplicates with this
   fingerprint.
3. **Short records can collide.** Benzene vs pyridine, two distinct
   8-9 byte records, have exact overlap 0.9230. Short records occupy few
   blocks, so their spectra are dominated by padding structure and can
   nearly coincide. On the full sample (206 distinct pairs), a threshold
   of 0.95 gives zero false-equals and catches every identical pair,
   but the margin rests on worst cases at 0.9230 and 0.9325, which is
   thin. Record length dependence is uncharacterised beyond this.

## Study 2: noise, monolithic vs per-coefficient (Aer, depolarizing)

The qhashrope lesson suggests decomposing: 12 separate 3-qubit SWAP
tests, one per spectral coefficient, recombining the per-coefficient
estimates as a product. Tested at the qhashrope noise level, p = 0.02,
against the 25-qubit monolithic SWAP test. Overlap estimates:

| Pair | Exact | Monolithic, noiseless | Decomposed, noiseless | Monolithic, p=0.02 | Decomposed, p=0.02 |
|---|---|---|---|---|---|
| DNA identical | 1.0000 | 1.0000 | 1.0000 | 0.6123 | 0.4191 |
| DNA 1 substitution | 0.7084 | 0.7153 | 0.7191 | 0.4263 | 0.3033 |
| DNA 10 substitutions | 0.0129 | 0.0283 | 0.0144 | 0.0083 | 0.0065 |
| Benzene vs cyclohexane | 0.0000 | 0.0142 | 0.0011 | 0.0000 | 0.0008 |

Findings:

1. Noiseless, both forms track the exact overlap (identical exactly 1).
2. **Under noise the decomposed form is worse, not better: 0.4191 vs
   0.6123 on the identical pair.** Each per-coefficient circuit
   contributes its own contraction factor (about 0.93), and the product
   compounds them: 0.93^12 is about 0.42, which is what the identical
   pair measures. This is the same compounding that defeated analog
   product recombination in qhashrope (0.93^24, identical pairs at
   0.59). qhashrope's decomposition works because its recombination is
   at the decision level under an error-correcting code (per-bit
   decisions, Golay radius-3 rule, up to 3 wrong bits tolerated).
   qfourierrope has no code, so it has no decision level to recombine
   at, and decomposition only multiplies analog error.
3. Noise hurts only the identical side in both forms; distinct pairs
   stay at the floor. Any threshold set from noiseless data (e.g. 0.95
   from Study 1) fails on identical pairs at p = 0.02 in either form.

## What this means for the project

The spectral phase fingerprint is a plausible exact-equality test for
long records in low noise, with two open problems now measured rather
than conjectured: (a) short-record spectral collisions, and (b) no
noise-robust recombination exists without an error-correcting
structure for phase fingerprints, which is the same open problem the
qhashrope deck records (a fingerprint code with a cheap preparation
circuit). Next steps, in order: record-length scaling of the collision
rate; more coefficients (K = 24) and magnitude-aware features; the
phase-code question. A hardware run is premature until the noise story
improves in simulation.

## Study 3: two-silo dedup at population scale (2026-11-11)

Question: does the fingerprint-only matching protocol work end to end
when the pair count is in the millions and the corpus is a real genome
with genuine near-repeats, not synthetic records? `exp_dedup.py`; raw
data `dedup_results.json`; framing and claim scope in `ADVANTAGE.md`.

Design: Silo A and Silo B hold 2,000 records each, 192-byte contiguous
slices of the E. coli K-12 MG1655 reference genome (NC_000913.3).
200 seeded Silo A records are planted in Silo B (the shared set); the
rest of Silo B is fresh slices. All 4,000,000 cross pairs scored by
exact overlap. Circuit checks on Aer (4096 shots): 12 planted
duplicates, and the 12 distinct pairs with the highest exact overlaps
in the full matrix (patched in by `circuit_hardest.py`; the first
run's hardest-pair selection had a masked-array indexing error, since
fixed in `exp_dedup.py`; the exact matrix results were unaffected).

Results:

- Duplicates: 200 of 200 recovered at overlap > 0.999999. Every
  duplicate sits at exactly 1.0000, and the 12 circuit-checked
  duplicates measure exactly 1.0000.
- False equals: 0 in 4,000,000 pairs.
- Closest distinct pairs in the full matrix, exact then measured:

| Exact | Measured (Aer) |
|---|---|
| 0.7555 | 0.7686 |
| 0.7136 | 0.7139 |
| 0.4581 | 0.4639 |
| 0.4374 | 0.4580 |
| 0.3956 | 0.4185 |
| 0.3886 | 0.3892 |
| 0.3839 | 0.3965 |
| 0.3699 | 0.4062 |
| 0.3688 | 0.3862 |
| 0.3672 | 0.3516 |
| 0.3619 | 0.3311 |
| 0.3598 | 0.3721 |

- Length sweep (500 fresh independent pairs per length): worst
  distinct overlap 0.0261 (64 B), 0.0154 (192 B), 0.0183 (1,024 B),
  0.0278 (4,096 B); medians at or below 1e-12.

Findings:

1. **The protocol separates a real corpus completely.** On 4M real
   pairs the duplicate floor (exactly 1.0) and the distinct ceiling
   (0.7555) leave a margin of 0.24, and the circuit reproduces it
   (worst distinct pair measures 0.7686; duplicates measure 1.0000).
   Any decision threshold inside (0.756, 1.0) classifies this corpus
   perfectly; the study reports the measured margin rather than
   fixing a threshold.
2. **The tail risk is genomic near-repeats, not random pairs.** Random
   independent pairs never exceeded 0.028 at any length in the sweep.
   The two pairs above 0.7 come from repeated regions of the genome:
   records that genuinely are near-copies. Population-scale scoring,
   not pair sampling, is what finds them.
3. **Circuit measurement tracks the exact overlap closely** (all 12
   hardest pairs within 0.04), so the exact matrix is a faithful
   proxy for the noiseless circuit at this size; noise and hardware
   contraction remain governed by Studies 1-2 and the hardware
   follow-up, and are the referee's real margin problem at deployment.

## Hardware follow-up (2026-11-10, ibm_fez; see HARDWARE.md)

A first hardware run was made the same day, ahead of the sequencing
suggested above, as a validation datapoint. It confirms the simulation
story on a device: distinct pairs sit at the floor (0.0122 against
0.0129 exact; 0.0000 for benzene vs cyclohexane), the identical pair
contracts harder than the p = 0.02 model predicts (0.3506 monolithic
against 0.6123 simulated), and the decomposed form is again worse than
the monolithic form (0.2287), with per-coefficient P(0) uniformly
0.932 to 0.949 showing the same compounding mechanism. No threshold is
claimed; the phase-code question stands.
