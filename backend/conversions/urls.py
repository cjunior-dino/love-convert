from django.urls import path

from .views import ConversionCreateView, ConversionDetailView, ConversionDownloadView

urlpatterns = [
    path("", ConversionCreateView.as_view(), name="conversion-create"),
    path(
        "<uuid:conversion_id>/",
        ConversionDetailView.as_view(),
        name="conversion-detail",
    ),
    path(
        "download/<uuid:conversion_id>/<str:filename>",
        ConversionDownloadView.as_view(),
        name="conversion-download",
    ),
]
