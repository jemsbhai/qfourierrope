"""Harvest the qfourierrope ibm_fez jobs (hardware_jobs.json).

Monolithic: overlap estimate max(0, 2*P(0) - 1) per pair.
Decomposed: per-coefficient P(0) values combined as the product of
max(0, 2*P(0) - 1) over the 12 coefficients, as in EXPERIMENTS.md.

Writes hardware_results.json and prints a summary table.
"""

import json
import time
from pathlib import Path

from qiskit_ibm_runtime import QiskitRuntimeService

HERE = Path(__file__).resolve().parent
TERMINAL = {"DONE", "ERROR", "CANCELLED"}


def counts_of(pub_result):
    for attr in vars(pub_result.data).values():
        if hasattr(attr, "get_counts"):
            return attr.get_counts()
    raise RuntimeError("no counts in pub result")


def p0_of(pub_result, shots):
    counts = counts_of(pub_result)
    return counts.get("0", 0) / shots


def main():
    record = json.loads((HERE / "hardware_jobs.json").read_text())
    shots = record["shots_per_circuit"]
    service = QiskitRuntimeService()
    jobs = {j["kind"]: service.job(j["job_id"]) for j in record["jobs"]}

    deadline = time.time() + 3 * 3600
    while time.time() < deadline:
        pending = [k for k, j in jobs.items() if str(j.status()) not in TERMINAL]
        print(f"[{time.strftime('%H:%M:%S')}] pending: {pending}", flush=True)
        if not pending:
            break
        time.sleep(60)

    results = {"backend": record["backend"], "shots_per_circuit": shots, "pairs": []}
    mono_job = next(j for j in record["jobs"] if j["kind"] == "monolithic")
    dec_job = next(j for j in record["jobs"] if j["kind"] == "decomposed")
    exact = {p["pair_id"]: p["exact_overlap"] for p in mono_job["pairs"]}

    mono_res = jobs["monolithic"].result() if str(jobs["monolithic"].status()) == "DONE" else None
    mono = {}
    if mono_res is not None:
        for i, p in enumerate(mono_job["pairs"]):
            p0 = p0_of(mono_res[i], shots)
            mono[p["pair_id"]] = {"p0": round(p0, 4), "overlap_est": round(max(0.0, 2 * p0 - 1), 4)}

    dec = {}
    if str(jobs["decomposed"].status()) == "DONE":
        dec_res = jobs["decomposed"].result()
        per_pair = {}
        for i, c in enumerate(dec_job["circuits"]):
            per_pair.setdefault(c["pair_id"], []).append(p0_of(dec_res[i], shots))
        for pid, p0s in per_pair.items():
            prod = 1.0
            for p in p0s:
                prod *= max(0.0, 2 * p - 1)
            dec[pid] = {"per_coefficient_p0": [round(p, 4) for p in p0s],
                        "overlap_est": round(prod, 4)}

    for pid in exact:
        results["pairs"].append({
            "pair_id": pid,
            "exact_overlap": exact[pid],
            "monolithic_hardware": mono.get(pid),
            "decomposed_hardware": dec.get(pid),
        })
    with open(HERE / "hardware_results.json", "w") as fh:
        json.dump(results, fh, indent=2)
    for p in results["pairs"]:
        print(f"{p['pair_id']:24s} exact={p['exact_overlap']:.4f} "
              f"mono_hw={p['monolithic_hardware']} dec_hw={p['decomposed_hardware']}", flush=True)


if __name__ == "__main__":
    main()
