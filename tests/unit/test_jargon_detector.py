from core.translator.jargon_detector import JargonDetector


def test_detects_marketing_jargon():
    jd = JargonDetector()
    found = jd.detect("CAC mục tiêu 8tr, ROAS ≥ 3.2x")
    terms = [t for t, _ in found]
    assert "CAC" in terms
    assert "ROAS" in terms


def test_filters_out_common_acronyms():
    jd = JargonDetector()
    found = jd.detect("DN của bạn ở VN, gặp CEO ngày T2")
    terms = [t for t, _ in found]
    assert "DN" not in terms
    assert "VN" not in terms
