from pathlib import Path

from rest_framework import serializers

from .i18n import request_language, translate
from .models import Conversion

MAX_FILE_SIZE = 10 * 1024 * 1024
ALLOWED_CONVERSIONS = {
    ".docx": {"markdown", "html", "pdf"},
    ".pdf": {"docx"},
}


class ConversionRequestSerializer(serializers.Serializer):
    file = serializers.FileField(required=True)
    output_format = serializers.ChoiceField(choices=Conversion.OutputFormat.values)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        language = request_language(self.context.get("request"))
        self.language = language
        self.fields["file"].error_messages.update(
            {
                "required": translate("validation.file_required", language),
                "null": translate("validation.file_required", language),
                "empty": translate("validation.file_required", language),
                "no_file": translate("validation.file_required", language),
            }
        )
        self.fields["output_format"].error_messages.update(
            {
                "required": translate("validation.output_required", language),
                "invalid_choice": translate("validation.output_invalid", language),
            }
        )

    def validate_file(self, uploaded_file):
        extension = Path(uploaded_file.name).suffix.lower()
        if extension not in ALLOWED_CONVERSIONS:
            raise serializers.ValidationError(
                translate("validation.file_type", self.language)
            )
        if uploaded_file.size > MAX_FILE_SIZE:
            raise serializers.ValidationError(
                translate("validation.max_size", self.language)
            )
        signature = uploaded_file.read(5)
        uploaded_file.seek(0)
        if extension == ".pdf" and not signature.startswith(b"%PDF-"):
            raise serializers.ValidationError(
                translate("validation.invalid_pdf", self.language)
            )
        if extension == ".docx" and not signature.startswith(b"PK"):
            raise serializers.ValidationError(
                translate("validation.invalid_docx", self.language)
            )
        return uploaded_file

    def validate(self, attrs):
        input_extension = Path(attrs["file"].name).suffix.lower()
        output_format = attrs["output_format"]
        if output_format not in ALLOWED_CONVERSIONS[input_extension]:
            if input_extension == ".pdf":
                message = translate("validation.pdf_output", self.language)
            else:
                message = translate("validation.docx_output", self.language)
            raise serializers.ValidationError({"output_format": message})
        return attrs
