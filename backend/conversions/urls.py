from django.urls import path

from .views import ConversionCreateView, ConversionDownloadView

urlpatterns = [
    path("", ConversionCreateView.as_view(), name="conversion-create"),
    path(
        "download/<uuid:conversion_id>/<str:filename>",
        ConversionDownloadView.as_view(),
        name="conversion-download",
    ),
]
