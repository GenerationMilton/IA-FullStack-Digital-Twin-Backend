import logging

from mangum import Mangum
from server import app

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

_asgi_handler = Mangum(app, lifespan="off")


def _is_http_event(event: object) -> bool:
    """True when the payload matches API Gateway, HTTP API, ALB, or CloudFront."""
    if not isinstance(event, dict):
        return False
    request_context = event.get("requestContext")
    if isinstance(request_context, dict):
        if "elb" in request_context or "http" in request_context:
            return True
    if "resource" in event and "requestContext" in event:
        return True
    if "version" in event and "requestContext" in event:
        return True
    records = event.get("Records")
    if isinstance(records, list) and records and isinstance(records[0], dict):
        return "cf" in records[0]
    return False


def handler(event, context):
    if not _is_http_event(event):
        keys = list(event.keys()) if isinstance(event, dict) else type(event).__name__
        logger.warning("Non-HTTP Lambda event; keys=%s", keys)
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": (
                '{"detail":"Expected an API Gateway (AWS_PROXY), HTTP API, ALB, or '
                'Function URL event. Use API Gateway proxy integration or test with '
                'the API Gateway proxy template—not the default hello-world event."}'
            ),
        }
    return _asgi_handler(event, context)