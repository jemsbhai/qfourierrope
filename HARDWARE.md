# IBM Quantum hardware results: first run on ibm_fez

Run 2026-11-10 on **ibm_fez** (156-qubit Heron r2), IBM Quantum
instance "qhashrope" (Open plan), SamplerV2, 4,096 shots per circuit.
Two jobs: the monolithic 25-qubit SWAP test for the four study pairs
(job dbpk4i5t7fqc7389j2tg), and the decomposed per-coefficient form
(12 independent 3-qubit SWAP tests per pair) for the identical and
1-substitution pairs (job dbpk4i8ou4as73ctqohg). Overlap estimates use
the same estimators as the simulation study in EXPERIMENTS.md:
max(0, 2*P(0) - 1) for the monolithic circuit, and the product of
max(0, 2*P(0) - 1) over the 12 coefficients for the decomposed form.

| Pair | Exact | Mono, sim p=0.02 | Mono, hardware | Decomp, sim p=0.02 | Decomp, hardware |
|---|---|---|---|---|---|
| DNA identical | 1.0000 | 0.6123 | 0.3506 | 0.4191 | 0.2287 |
| DNA 1 substitution | 0.7084 | 0.3797 | 0.2690 | 0.2686 | 0.1501 |
| DNA 10 substitutions | 0.0129 | 0.0000 | 0.0122 | n/a | n/a |
| benzene vs cyclohexane | 0.0000 | 0.0135 | 0.0000 | n/a | n/a |

## Reading

- Distinct pairs sit at the floor on hardware, matching simulation:
  0.0122 measured against 0.0129 exact for the 10-substitution pair,
  and 0.0000 for benzene vs cyclohexane.
- The identical pair contracts harder on the device than under the
  p = 0.02 depolarizing model: 0.3506 measured against 0.6123
  simulated (monolithic P(0) 0.6753).
- The decomposed form is again worse than the monolithic form on
  hardware (0.2287 vs 0.3506 for the identical pair), confirming the
  simulation's negative result on a device. The mechanism is visible
  in the per-coefficient values: P(0) is uniformly 0.932 to 0.949
  across the 12 coefficients for the identical pair, i.e. each small
  circuit contributes a fidelity factor of about 0.88 in (2*P(0) - 1),
  and the factors compound in the product (0.88^12 is about 0.22).
- No decision threshold is claimed. The open problem is unchanged and
  now has a hardware datapoint: a phase fingerprint code, analogous
  to the Golay code that makes qhashrope's decomposition work at the
  decision level, with a cheap preparation circuit.

Raw record: `hardware_jobs.json` (submission),
`hardware_results.json` (harvested values).
Scripts: `submit_hardware.py`, `retrieve_hardware.py`.
