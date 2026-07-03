from app.config import settings
from app.summary.severity import bucket_severity


def test_buckets():
    assert bucket_severity(0.0) == "minor"
    assert bucket_severity(settings.severity_minor - 1e-9) == "minor"
    assert bucket_severity(settings.severity_minor) == "moderate"
    assert bucket_severity(settings.severity_moderate - 1e-9) == "moderate"
    assert bucket_severity(settings.severity_moderate) == "significant"
    assert bucket_severity(0.5) == "significant"
