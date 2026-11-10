"""Spectral fingerprints for qfourierrope.

qhashrope fingerprints a record with position-seeded block hashes folded
to a 12-bit message and expanded by the Golay (24,12,8) code into basis
states: exact, but a basis state carries no phase information, so the
construction has no quantum communication advantage (the stated
limitation in the qhashrope README).

qfourierrope explores the complementary direction: a *phase* fingerprint
derived from the spectrum of the record's block signal.

Pipeline:
  1. Split the record into N_BLOCKS blocks; hash each block with a
     position-seeded hash (splitmix64 finalizer over the block bytes,
     seeded by block index), the same seeding discipline as qhashrope.
  2. Treat the block-hash sequence as a discrete signal x[j] in [0, 1).
  3. Take the DFT of x. The fingerprint angles are the phases of the
     first K spectral coefficients, theta_j = arg X[j], j = 1..K
     (the DC coefficient is dropped; its phase is always 0).
  4. The quantum fingerprint is the product state with one qubit per
     spectral coefficient, (|0> + e^{i theta_j} |1>) / sqrt(2).

The overlap of two fingerprints factorises over coefficients:

    |<psi(a)|psi(b)>|^2 = prod_j cos^2( (theta_j(a) - theta_j(b)) / 2 )

so identical records give overlap exactly 1, and records whose block
spectra differ get an overlap strictly below 1 that decreases with the
number and size of the spectral phase differences. Unlike qhashrope
there is no error-correcting code and no guaranteed minimum distance:
the decision threshold is an empirical question, and quantifying the
false-equal rate of spectral fingerprints is the research problem this
repo exists to measure. Nothing here claims qhashrope's exactness.
"""

from __future__ import annotations

import numpy as np

N_BLOCKS = 24
K_COEFFS = 12  # spectral coefficients used, matching qhashrope's 12-symbol width

_MASK64 = (1 << 64) - 1


def _splitmix64(x: int) -> int:
    x = (x + 0x9E3779B97F4A7C15) & _MASK64
    x = ((x ^ (x >> 30)) * 0xBF58476D1CE4E5B9) & _MASK64
    x = ((x ^ (x >> 27)) * 0x94D049BB133111EB) & _MASK64
    return x ^ (x >> 31)


def block_hashes(data: bytes, n_blocks: int = N_BLOCKS) -> list[int]:
    """Position-seeded 64-bit hash of each block of `data`."""
    if n_blocks <= 0:
        raise ValueError("n_blocks must be positive")
    blocks = np.array_split(np.frombuffer(data, dtype=np.uint8), n_blocks)
    out: list[int] = []
    for j, blk in enumerate(blocks):
        h = _splitmix64(j * 0x2545F4914F6CDD1D & _MASK64)
        for b in blk.tolist():
            h = _splitmix64(h ^ (int(b) + 0x9E3779B97F4A7C15) & _MASK64)
        out.append(h)
    return out


def block_signal(data: bytes, n_blocks: int = N_BLOCKS) -> np.ndarray:
    """The block-hash sequence as a signal in [0, 1)."""
    return np.array([h / float(1 << 64) for h in block_hashes(data, n_blocks)])


def spectral_angles(data: bytes, k: int = K_COEFFS) -> np.ndarray:
    """Phases of the first k non-DC DFT coefficients of the block signal."""
    x = block_signal(data)
    spectrum = np.fft.fft(x)
    coeffs = spectrum[1 : k + 1]
    return np.angle(coeffs)  # in (-pi, pi]


def classical_overlap(angles_a: np.ndarray, angles_b: np.ndarray) -> float:
    """|<psi(a)|psi(b)>|^2 computed classically, for verification."""
    d = (angles_a - angles_b) / 2.0
    return float(np.prod(np.cos(d) ** 2))
