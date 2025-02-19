from django.core.exceptions import PermissionDenied as django_PermissionDenied
from django.http import Http404
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.status import HTTP_500_INTERNAL_SERVER_ERROR
from rest_framework.views import exception_handler

def get_exception_type(exception):
    """
    Method exception_handler() handles Django's built-in `Http404` and `PermissionDenied` exceptions,
    but only returns exception details. I'm doing the same check and return, the exception type, that it uses
    """
    exception_type = exception
    if isinstance(exception, Http404):
        exception_type = NotFound()
    elif isinstance(exception, django_PermissionDenied):
        exception_type = PermissionDenied()
    return exception_type.__class__.__name__

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        error_detail = None
        if isinstance(response.data, (list, tuple)):
            if len(response.data) > 1:
                error_detail = response.data
            else:
                error_detail = response.data[0]
        elif isinstance(response.data, dict):
            detail = response.data.get('detail', '')

            if hasattr(detail, 'code'):
                error_detail = str(detail)
            else:
                error_detail = detail

        response.data = {
            "exception": get_exception_type(exc),
            "exception_detail": error_detail or exc.__dict__["detail"] or None,
            "status_code": response.status_code,
        }

    return response
