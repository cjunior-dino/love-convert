from pathlib import Path

from rest_framework import serializers

from .models import Conversion

MAX_FILE_SIZE = 10 * 1024 * 1024
ALLOWED_CONVERSIONS = {
    ".docx": {"markdown", "html", "pdf"},
    ".pdf": {"docx"},
}


class ConversionRequestSerializer(serializers.Serializer):
    file = serializers.FileField(required=True)
    output_format = serializers.ChoiceField(choices=Conversion.OutputFormat.values)

    def validate_file(self, uploaded_file):
        if Path(uploaded_file.name).suffix.lower() not in ALLOWED_CONVERSIONS:
            raise serializers.ValidationError("Apenas arquivos .docx e .pdf são aceitos.")
        if uploaded_file.size > MAX_FILE_SIZE:
            raise serializers.ValidationError("O arquivo deve ter no máximo 10 MB.")
        return uploaded_file

    def validate(self, attrs):
        input_extension = Path(attrs["file"].name).suffix.lower()
        output_format = attrs["output_format"]
        if output_format not in ALLOWED_CONVERSIONS[input_extension]:
            if input_extension == ".pdf":
                message = "Arquivos PDF só podem ser convertidos para DOCX."
            else:
                message = "Arquivos DOCX podem ser convertidos para Markdown, HTML ou PDF."
            raise serializers.ValidationError({"output_format": message})
        return attrs
