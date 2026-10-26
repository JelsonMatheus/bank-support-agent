import logging

import redis
from django.conf import settings
from django.db import connection
from django.http import JsonResponse
from django.views.decorators.http import require_GET

logger = logging.getLogger(__name__)


def _check_database() -> bool:
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        return True
    except Exception:
        logger.exception("Health check: database unavailable")
        return False


def _check_broker() -> bool:
    try:
        client = redis.Redis.from_url(settings.CELERY_BROKER_URL, socket_connect_timeout=1)
        return bool(client.ping())
    except Exception:
        logger.exception("Health check: broker unavailable")
        return False


@require_GET
def health(request):
    checks = {"database": _check_database(), "broker": _check_broker()}
    healthy = all(checks.values())
    return JsonResponse(
        {"status": "ok" if healthy else "degraded", "checks": checks},
        status=200 if healthy else 503,
    )
