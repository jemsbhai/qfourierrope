"""qfourierrope: spectral phase fingerprints for quantum equality testing.

Based on qhashrope (github.com/jemsbhai/qhashrope): same problem (decide
whether two large records are identical without moving the records),
complementary fingerprint. Where qhashrope encodes a Golay-expanded
message into basis states for an exact decision, qfourierrope encodes
the phases of the record's block-spectrum into a phase fingerprint,
the direction the qhashrope README names as the route to a quantum
communication advantage.
"""

from .spectral import block_signal, classical_overlap, spectral_angles
from .quantum_verify import estimate_overlap

__all__ = [
    "block_signal",
    "spectral_angles",
    "classical_overlap",
    "estimate_overlap",
]

__version__ = "0.1.0"
