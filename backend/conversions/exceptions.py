from rest_framework.response import Response
from rest_framework.views import exception_handler

from .i18n import request_language, translate


def api_exception_handler(exc, context):
    language = request_language(context.get("request"))
    response = exception_handler(exc, context)
    if response is None:
        return Response(
            {"success": False, "error": translate("request.failed", language)},
            status=500,
        )

    detail = response.data.get("detail") if isinstance(response.data, dict) else None
    if detail:
        key = "request.not_found" if response.status_code == 404 else "request.failed"
        response.data = {"success": False, "error": translate(key, language)}
    return response
