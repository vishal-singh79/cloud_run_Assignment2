from deploy_app.main import calculate_health_score


def test_health_score_excellent():
    score = calculate_health_score(
        cpu=10,
        mem=20,
        uptime=4000
    )
    assert score >= 85


def test_health_score_high_cpu():
    score = calculate_health_score(
        cpu=95,
        mem=30,
        uptime=100
    )
    assert score < 60


def test_health_score_high_memory():
    score = calculate_health_score(
        cpu=20,
        mem=95,
        uptime=100
    )
    assert score < 60


def test_health_score_never_negative():
    score = calculate_health_score(
        cpu=100,
        mem=100,
        uptime=0
    )
    assert score >= 0


def test_health_score_never_above_100():
    score = calculate_health_score(
        cpu=0,
        mem=0,
        uptime=100000
    )
    assert score <= 100
