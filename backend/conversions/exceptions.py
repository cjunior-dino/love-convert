from rest_framework.response import Response
from rest_framework.views import exception_handler


def api_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return Response(
            {"success": False, "error": "Não foi possível processar a solicitação."},
            status=500,
        )

    detail = response.data.get("detail") if isinstance(response.data, dict) else None
    if detail:
        response.data = {"success": False, "error": str(detail)}
    return response
