"""SWAP-test comparison of qfourierrope spectral phase fingerprints.

Each fingerprint qubit is prepared as (|0> + e^{i theta_j} |1>) / sqrt(2)
(Hadamard, then a phase rotation by theta_j). A standard SWAP test on
the two K-qubit fingerprints estimates |<psi(a)|psi(b)>|^2 as
P(0) = (1 + |<psi(a)|psi(b)>|^2) / 2 on the ancilla.

No decision threshold is fixed in this module: measuring the overlap
distribution of identical vs distinct records (and where a defensible
threshold sits) is the open empirical question of the project.
"""

from __future__ import annotations

import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator

from .spectral import classical_overlap, spectral_angles


def fingerprint_circuit(angles: np.ndarray, name: str = "fp") -> QuantumCircuit:
    qc = QuantumCircuit(len(angles), name=name)
    for j, theta in enumerate(angles):
        qc.h(j)
        qc.p(float(theta), j)
    return qc


def swap_test_circuit(angles_a: np.ndarray, angles_b: np.ndarray) -> QuantumCircuit:
    k = len(angles_a)
    qc = QuantumCircuit(1 + 2 * k, 1)
    anc = 0
    reg_a = list(range(1, 1 + k))
    reg_b = list(range(1 + k, 1 + 2 * k))
    qc.compose(fingerprint_circuit(angles_a), qubits=reg_a, inplace=True)
    qc.compose(fingerprint_circuit(angles_b), qubits=reg_b, inplace=True)
    qc.h(anc)
    for x, y in zip(reg_a, reg_b):
        qc.cswap(anc, x, y)
    qc.h(anc)
    qc.measure(anc, 0)
    return qc


def estimate_overlap(
    data_a: bytes, data_b: bytes, shots: int = 4096, seed: int = 20261110
) -> dict:
    """Run the SWAP test in simulation and return measured + exact values."""
    angles_a = spectral_angles(data_a)
    angles_b = spectral_angles(data_b)
    qc = swap_test_circuit(angles_a, angles_b)
    sim = AerSimulator(seed_simulator=seed)
    counts = sim.run(transpile(qc, sim), shots=shots).result().get_counts()
    p0 = counts.get("0", 0) / shots
    measured_overlap = max(0.0, 2.0 * p0 - 1.0)
    return {
        "p0": p0,
        "measured_overlap": measured_overlap,
        "exact_overlap": classical_overlap(angles_a, angles_b),
        "shots": shots,
    }
