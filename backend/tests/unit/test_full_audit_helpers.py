from tools.full_audit import calculate_weighted_score, score_to_grade


def test_calculate_weighted_score():
    scores = {
        "technical": 80,
        "content": 90,
    }
    weights = {
        "technical": 0.6,
        "content": 0.4,
    }
    assert calculate_weighted_score(scores, weights) == 84.0


def test_score_to_grade():
    assert score_to_grade(95) == "A"
    assert score_to_grade(82) == "B"
    assert score_to_grade(74) == "C"
    assert score_to_grade(65) == "D"
    assert score_to_grade(40) == "F"
