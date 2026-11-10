"""Submit qfourierrope's first hardware jobs to IBM Quantum (ibm_fez).

Two jobs, SamplerV2, 4096 shots per circuit, 2026-11-10:

  monolithic: the 25-qubit SWAP test for the 4 study pairs (identical,
  1 substitution, 10 substitutions, benzene vs cyclohexane). Simulation
  at depolarizing p = 0.02 contracted the identical pair to 0.6123
  (EXPERIMENTS.md); this measures where the device lands.

  decomposed: the 12 per-coefficient 3-qubit SWAP tests for the
  identical and 1-substitution pairs (24 circuits). Simulation says
  decomposition is worse under noise (0.4191 for identical); this
  checks the device against that prediction.

Writes hardware_jobs.json immediately after submission.
Analysis lives in retrieve_hardware.py.
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from qiskit import QuantumCircuit
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler

from qfourierrope.quantum_verify import fingerprint_circuit, swap_test_circuit
from qfourierrope.spectral import classical_overlap, spectral_angles

BACKEND_NAME = "ibm_fez"
SHOTS = 4096
OUT = Path(__file__).with_name("hardware_jobs.json")

DNA_A = (b"ACGTGCAATGCCGTTAACGGATCCTAGGCAATCGGATCCATTAACCGG" * 4)
DNA_1SUB = DNA_A[:17] + b"T" + DNA_A[18:]
_DNA_10 = bytearray(DNA_A)
for _i in range(0, len(_DNA_10), 19):
    _DNA_10[_i] = ord("T") if _DNA_10[_i] != ord("T") else ord("A")

PAIRS = [
    ("dna_identical", "DNA identical", DNA_A, DNA_A),
    ("dna_1sub", "DNA 1 substitution", DNA_A, DNA_1SUB),
    ("dna_10sub", "DNA 10 substitutions", DNA_A, bytes(_DNA_10)),
    ("benzene_vs_cyclohexane", "benzene vs cyclohexane", b"c1ccccc1", b"C1CCCCC1"),
]
DECOMPOSED_PAIRS = ["dna_identical", "dna_1sub"]


def per_coefficient_circuit(theta_a: float, theta_b: float) -> QuantumCircuit:
    qc = QuantumCircuit(3, 1)
    qc.compose(fingerprint_circuit([theta_a]), qubits=[1], inplace=True)
    qc.compose(fingerprint_circuit([theta_b]), qubits=[2], inplace=True)
    qc.h(0)
    qc.cswap(0, 1, 2)
    qc.h(0)
    qc.measure(0, 0)
    return qc


def main():
    service = QiskitRuntimeService()
    backend = service.backend(BACKEND_NAME)
    pm = generate_preset_pass_manager(backend=backend, optimization_level=1)
    sampler = Sampler(mode=backend)

    record = {
        "backend": BACKEND_NAME,
        "shots_per_circuit": SHOTS,
        "submitted_at_utc": datetime.now(timezone.utc).isoformat(),
        "jobs": [],
    }

    angles = {pid: (spectral_angles(a), spectral_angles(b)) for pid, _, a, b in PAIRS}

    mono_circuits = [swap_test_circuit(*angles[pid]) for pid, *_ in PAIRS]
    job = sampler.run(pm.run(mono_circuits), shots=SHOTS)
    record["jobs"].append({
        "kind": "monolithic",
        "job_id": job.job_id(),
        "pairs": [{"pair_id": pid, "label": label,
                   "exact_overlap": classical_overlap(*angles[pid])}
                  for pid, label, _, _ in PAIRS],
    })
    print(f"monolithic: job {job.job_id()} (4 circuits)", flush=True)

    dec_circuits, dec_index = [], []
    for pid, label, _, _ in PAIRS:
        if pid not in DECOMPOSED_PAIRS:
            continue
        ang_a, ang_b = angles[pid]
        for j in range(len(ang_a)):
            dec_circuits.append(per_coefficient_circuit(float(ang_a[j]), float(ang_b[j])))
            dec_index.append({"pair_id": pid, "coefficient": j})
    job = sampler.run(pm.run(dec_circuits), shots=SHOTS)
    record["jobs"].append({
        "kind": "decomposed",
        "job_id": job.job_id(),
        "circuits": dec_index,
        "pairs": [{"pair_id": pid, "label": label,
                   "exact_overlap": classical_overlap(*angles[pid])}
                  for pid, label, _, _ in PAIRS if pid in DECOMPOSED_PAIRS],
    })
    print(f"decomposed: job {job.job_id()} ({len(dec_circuits)} circuits)", flush=True)

    with open(OUT, "w") as fh:
        json.dump(record, fh, indent=2)
    print(f"wrote {OUT.name}: {len(record['jobs'])} jobs")


if __name__ == "__main__":
    main()
