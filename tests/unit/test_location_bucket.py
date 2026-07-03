from app.summary.location import bucket_location


def test_corners():
    assert bucket_location(0.1, 0.1) == "upper-left"
    assert bucket_location(0.9, 0.1) == "upper-right"
    assert bucket_location(0.1, 0.9) == "lower-left"
    assert bucket_location(0.9, 0.9) == "lower-right"


def test_center_and_bands():
    assert bucket_location(0.5, 0.5) == "center"
    assert bucket_location(0.1, 0.5) == "left"
    assert bucket_location(0.9, 0.5) == "right"
    assert bucket_location(0.5, 0.1) == "upper"
    assert bucket_location(0.5, 0.9) == "lower"


def test_boundaries():
    # exactly on the 1/3 line belongs to the center band
    assert bucket_location(1 / 3, 1 / 3) == "center"
    assert bucket_location(2 / 3, 2 / 3) == "center"
