"""Noise behaviour of qfourierrope: monolithic vs per-coefficient circuits.

qhashrope's lesson: under depolarizing noise the monolithic circuit's
signal contracts below threshold, and the fix is decomposition plus
decision-level recombination. qfourierrope's overlap factorises over
the 12 spectral coefficients, so it has a natural decomposition: 12
independent 3-qubit SWAP tests (ancilla + one coefficient qubit from
each party), each estimating cos^2(dtheta_j / 2) = 2*P(0)_j - 1, with
the overlap estimate the product of the clipped per-coefficient values.

Settings per pair: monolithic (25 qubits) and decomposed (12 x 3
qubits), each noiseless and at depolarizing p = 0.02 (the qhashrope
noise model and level), 4096 shots per circuit, Aer MPS.

No threshold is applied anywhere in this script; it reports estimates.
"""

import json

import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator

from qfourierrope import qnoise
from qfourierrope.quantum_verify import fingerprint_circuit
from qfourierrope.spectral import classical_overlap, spectral_angles

DNA_A = (b"ACGTGCAATGCCGTTAACGGATCCTAGGCAATCGGATCCATTAACCGG" * 4)
DNA_1SUB = DNA_A[:17] + b"T" + DNA_A[18:]
DNA_10SUB_B = bytearray(DNA_A)
for i in range(0, len(DNA_10SUB_B), 19):
    DNA_10SUB_B[i] = ord("T") if DNA_10SUB_B[i] != ord("T") else ord("A")

PAIRS = [
    ("DNA identical", DNA_A, DNA_A, True),
    ("DNA 1 substitution", DNA_A, DNA_1SUB, False),
    ("DNA 10 substitutions", DNA_A, bytes(DNA_10SUB_B), False),
    ("benzene vs cyclohexane", b"c1ccccc1", b"C1CCCCC1", False),
]
SHOTS = 4096
P_NOISE = 0.02


def run(qc: QuantumCircuit, sim: AerSimulator) -> dict:
    return sim.run(transpile(qc, sim), shots=SHOTS).result().get_counts()


def monolithic(angles_a, angles_b, sim) -> float:
    from qfourierrope.quantum_verify import swap_test_circuit

    counts = run(swap_test_circuit(angles_a, angles_b), sim)
    p0 = counts.get("0", 0) / SHOTS
    return max(0.0, 2.0 * p0 - 1.0)


def decomposed(angles_a, angles_b, sim) -> float:
    factors = []
    for j in range(len(angles_a)):
        qc = QuantumCircuit(3, 1)
        qc.compose(fingerprint_circuit(angles_a[j:j + 1]), qubits=[1], inplace=True)
        qc.compose(fingerprint_circuit(angles_b[j:j + 1]), qubits=[2], inplace=True)
        qc.h(0)
        qc.cswap(0, 1, 2)
        qc.h(0)
        qc.measure(0, 0)
        counts = run(qc, sim)
        p0 = counts.get("0", 0) / SHOTS
        factors.append(min(1.0, max(0.0, 2.0 * p0 - 1.0)))
    return float(np.prod(factors))


def main() -> None:
    sims = {
        "noiseless": AerSimulator(method="matrix_product_state", seed_simulator=20261110),
        "p0.02": AerSimulator(
            method="matrix_product_state", seed_simulator=20261110,
            noise_model=qnoise.depolarizing(P_NOISE),
        ),
    }
    results = []
    for name, a, b, _ in PAIRS:
        ang_a, ang_b = spectral_angles(a), spectral_angles(b)
        row = {"pair": name, "exact_overlap": classical_overlap(ang_a, ang_b)}
        for label, sim in sims.items():
            row[f"monolithic_{label}"] = monolithic(ang_a, ang_b, sim)
            row[f"decomposed_{label}"] = decomposed(ang_a, ang_b, sim)
        results.append(row)
        print(row)
    with open("noise_results.json", "w") as f:
        json.dump({"p_noise": P_NOISE, "shots": SHOTS, "pairs": results}, f, indent=2)
    print("wrote noise_results.json")


if __name__ == "__main__":
    main()
