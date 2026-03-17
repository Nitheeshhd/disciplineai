from datetime import date, timedelta

from app.services.productivity_service import ProductivityService


def test_calculate_streak():
    today = date.today()
    totals = {
        today: 2.0,
        today - timedelta(days=1): 1.5,
        today - timedelta(days=2): 0.5,
        today - timedelta(days=4): 3.0,
    }
    streak = ProductivityService.calculate_streak(totals, target_day=today)
    assert streak == 3


def test_moving_average():
    today = date.today()
    totals = {today - timedelta(days=i): float(i + 1) for i in range(7)}
    avg = ProductivityService.calculate_moving_average(totals, days=7)
    assert avg == 4.0


def test_anomaly_detection():
    today = date.today()
    totals = {
        today - timedelta(days=7): 1.0,
        today - timedelta(days=6): 1.5,
        today - timedelta(days=5): 1.2,
        today - timedelta(days=4): 1.3,
        today - timedelta(days=3): 1.4,
        today - timedelta(days=2): 1.1,
        today - timedelta(days=1): 1.6,
        today: 8.0,
    }
    assert ProductivityService.detect_anomaly(totals) is True
