import numpy as np

from qfourierrope.spectral import classical_overlap, spectral_angles

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
