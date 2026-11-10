import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np  # noqa: E402

from qfourierrope.spectral import classical_overlap, spectral_angles  # noqa: E402

RECORD = b"The quick brown fox jumps over the lazy dog" * 8


def test_identical_records_have_identical_angles():
    a = spectral_angles(RECORD)
    b = spectral_angles(RECORD)
    assert np.allclose(a, b)
    assert classical_overlap(a, b) == 1.0


def test_distinct_records_overlap_below_one():
    a = spectral_angles(RECORD)
    b = spectral_angles(b"Pack my box with five dozen liquor jugs" * 8)
    ov = classical_overlap(a, b)
    assert 0.0 <= ov < 1.0


if __name__ == "__main__":
    test_identical_records_have_identical_angles()
    test_distinct_records_overlap_below_one()
    print("2 passed")
