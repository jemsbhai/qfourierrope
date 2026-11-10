"""Simple Aer noise models: depolarizing error on all gates.

Mirrors qhashrope.qnoise, extended with the phase gate ("p") that the
spectral fingerprint preparation uses.
"""

from qiskit_aer.noise import NoiseModel, depolarizing_error

_ONE_QUBIT = ["h", "x", "z", "ry", "u", "u1", "u2", "u3", "id", "sx", "p", "rz"]
_TWO_QUBIT = ["cx", "swap"]
_THREE_QUBIT = ["cswap"]  # Fredkin gate acts on 3 qubits


def depolarizing(p: float) -> NoiseModel:
    """Depolarizing noise with probability p on every gate."""
    model = NoiseModel()
    if p > 0:
        model.add_all_qubit_quantum_error(depolarizing_error(p, 1), _ONE_QUBIT)
        model.add_all_qubit_quantum_error(depolarizing_error(p, 2), _TWO_QUBIT)
        model.add_all_qubit_quantum_error(depolarizing_error(p, 3), _THREE_QUBIT)
    return model
