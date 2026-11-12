# The advantage claim, stated exactly

qfourierrope is a quantum fingerprinting protocol for one job: two
parties each hold a record, a referee must answer one bit, "same record
or not", and the records themselves must not move. This document states
the advantage claim precisely, including where it does not apply.

## The model

Simultaneous message passing (SMP): Alice and Bob each send one message
to a referee, who answers. No shared randomness, no shared secret, no
interaction between Alice and Bob. This is the model of two institutions
that can both talk to a coordinator but have no prior trust setup with
each other, and of a coordinator who should learn nothing beyond the
answer.

## The separation (proven, not projected)

- Classical: any SMP protocol for equality on n-bit inputs without
  shared randomness needs messages of Omega(sqrt(n)) bits (Newman and
  Szegedy, 1996). For the 192-byte (1,536-bit) records used in this
  repo's studies, that floor is about 39 bits per fingerprint for the
  best possible classical protocol in this model, and it grows as
  sqrt(n).
- Quantum: fingerprints of O(log n) qubits suffice (Buhrman, Cleve,
  Watrous and de Wolf, "Quantum Fingerprinting", Physical Review
  Letters 87, 167902, 2001). The qfourierrope fingerprint is 12 qubits
  at any record length, because the spectral construction fixes the
  coefficient count; the communication cost does not grow with the
  record at all.

That is an exponential separation in communication, in a named model,
with a published lower bound on the classical side. It is the claim
this project makes, and it is the only advantage claim this project
makes.

## The privacy bound (also a theorem)

By Holevo's theorem (1973), at most 12 bits of classical information
are accessible from a 12-qubit fingerprint, by any measurement,
anywhere, ever. The referee, or anyone who intercepts the fingerprints,
learns the equality answer and provably almost nothing about records of
1,536 bits or more. A classical hash database carries no such bound: a
stolen fingerprint list can be dictionary-attacked offline. A stolen
quantum fingerprint cannot even be copied (no-cloning), and what little
it holds is capped by Holevo.

## What is NOT claimed

- No computational speedup. The fingerprint overlap has a closed
  classical form, prod_j cos^2((theta_j(a) - theta_j(b)) / 2), and a
  classical computer evaluates it in microseconds. If your problem is
  "compute this number", use a laptop.
- No advantage where shared randomness or a trusted shared hash is
  available: with shared randomness, classical SMP fingerprints are
  also short. The separation lives in the no-shared-randomness model
  above, which is the model that matches institutions without a prior
  trust setup.
- No error-correcting guarantee. The original quantum fingerprinting
  construction uses an error-correcting code to bound its error rate.
  This spectral construction does not, so its error behaviour is an
  empirical question. That is why this repo measures it: prototype
  pairs, a distribution study, a noise study, hardware runs on
  ibm_fez, and Study 3 (exp_dedup.py), a full two-silo matching run
  over 4,000 records of a real genome with 200 planted shared records,
  scored on all 4,000,000 cross pairs.

## Measured behaviour relevant to the protocol

Study 3 (2026-11-11, exp_dedup.py, raw data in dedup_results.json): two
silos of 2,000 records each, 192-byte contiguous slices of the E. coli
K-12 MG1655 reference genome, 200 records planted in both silos, all
4,000,000 cross pairs scored by exact overlap.

- All 200 planted duplicates recovered; every duplicate sits at overlap
  exactly 1.0000, and 12 of them run through the actual SWAP-test
  circuit (Aer, 4096 shots) measure exactly 1.0000.
- Zero false equals across all 4,000,000 pairs.
- The closest distinct pair in the full matrix reaches 0.7555. It is a
  near-repeat region of the genome (E. coli carries repeated elements),
  i.e. the worst case is two records that genuinely are near-copies.
  Through the circuit it measures 0.7686, a margin of 0.23 below the
  duplicate floor. The next closest distinct pair is 0.7136.
- Length sweep, 500 fresh independent pairs per length: worst distinct
  overlap 0.0261 at 64 bytes, 0.0154 at 192, 0.0183 at 1,024, 0.0278 at
  4,096; medians at or below 1e-12. Typical distinct pairs are not the
  risk; genome-scale near-repeats, found only by scoring millions of
  pairs, are the tail that matters, and they still separate.

## Known limits, measured

- Exact equality is the protocol's job. Identical records give overlap
  exactly 1 by construction; everything else is separation margin.
- Near-duplicates are the hard case: one substitution in a 192-byte
  record already moves the overlap to about 0.71, because one changed
  block changes the whole spectrum. This is an equality protocol, not
  a similarity search.
- Short records can collide: benzene vs pyridine, two distinct short
  molecules, measure 0.9230. The length sweep in Study 3 shows how the
  separation widens with record length.
- On current hardware the identical-pair overlap contracts (0.3506 on
  ibm_fez for the monolithic circuit), harder than the p = 0.02 noise
  model predicts. The protocol's decision margin must be read against
  device numbers, not simulator numbers, before any deployment claim.
