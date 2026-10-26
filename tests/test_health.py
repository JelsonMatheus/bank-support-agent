import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_health_returns_ok_when_all_checks_pass(client):
    response = client.get(reverse("health"))

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "checks": {"database": True, "broker": True},
    }


@pytest.mark.django_db
def test_health_returns_503_when_database_is_down(client, monkeypatch):
    monkeypatch.setattr("config.views._check_database", lambda: False)

    response = client.get(reverse("health"))

    assert response.status_code == 503
    assert response.json()["status"] == "degraded"
    assert response.json()["checks"]["database"] is False


def test_health_rejects_post(client):
    response = client.post(reverse("health"))

    assert response.status_code == 405