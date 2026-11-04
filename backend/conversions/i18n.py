from __future__ import annotations

from typing import Any


DEFAULT_LANGUAGE = "pt-br"
SUPPORTED_LANGUAGES = {"pt-br", "en", "es-419"}

MESSAGES: dict[str, dict[str, str]] = {
    "pt-br": {
        "validation.file_required": "Envie um arquivo para conversão.",
        "validation.output_required": "Escolha o formato de saída.",
        "validation.output_invalid": "O formato de saída selecionado não é válido.",
        "validation.file_type": "Apenas arquivos .docx e .pdf são aceitos.",
        "validation.max_size": "O arquivo deve ter no máximo 10 MB.",
        "validation.invalid_pdf": "O conteúdo do arquivo PDF não é válido.",
        "validation.invalid_docx": "O conteúdo do arquivo DOCX não é válido.",
        "validation.pdf_output": "Arquivos PDF só podem ser convertidos para DOCX.",
        "validation.docx_output": "Arquivos DOCX podem ser convertidos para Markdown, HTML ou PDF.",
        "validation.invalid_data": "Dados inválidos.",
        "queue.unavailable": "O serviço de conversão está temporariamente indisponível.",
        "request.failed": "Não foi possível processar a solicitação.",
        "request.not_found": "O recurso solicitado não foi encontrado.",
        "task.max_attempts": "A conversão excedeu o número máximo de tentativas.",
        "task.invalid_source": "O arquivo de origem não é válido.",
        "task.missing_source": "O arquivo de origem não foi encontrado.",
        "task.generic_failure": "Não foi possível converter o arquivo.",
        "service.unsupported": "Esta combinação de formatos não é suportada.",
        "service.pandoc_missing": "O Pandoc não está instalado ou não foi encontrado no PATH.",
        "service.pandoc_failed": "O Pandoc não conseguiu converter o documento.",
        "service.libreoffice_missing": "O LibreOffice não está instalado ou não foi encontrado no PATH. No WSL/Ubuntu, execute: sudo apt install libreoffice-writer",
        "service.pdf_timeout": "A conversão para PDF excedeu o tempo limite de 120 segundos.",
        "service.libreoffice_failed": "O LibreOffice não conseguiu converter o documento em PDF.{detail}",
        "service.pdf_not_generated": "O arquivo PDF não foi gerado.",
        "service.pdf2docx_missing": "A dependência pdf2docx não está instalada. Execute: python -m pip install -r requirements.txt",
        "service.pdf_to_docx_failed": "Não foi possível converter o PDF em DOCX. Verifique se o arquivo é válido e não está protegido.",
        "service.docx_not_generated": "O arquivo DOCX não foi gerado.",
    },
    "en": {
        "validation.file_required": "Upload a file to convert.",
        "validation.output_required": "Choose an output format.",
        "validation.output_invalid": "The selected output format is not valid.",
        "validation.file_type": "Only .docx and .pdf files are accepted.",
        "validation.max_size": "The file must be no larger than 10 MB.",
        "validation.invalid_pdf": "The PDF file content is not valid.",
        "validation.invalid_docx": "The DOCX file content is not valid.",
        "validation.pdf_output": "PDF files can only be converted to DOCX.",
        "validation.docx_output": "DOCX files can be converted to Markdown, HTML, or PDF.",
        "validation.invalid_data": "Invalid data.",
        "queue.unavailable": "The conversion service is temporarily unavailable.",
        "request.failed": "The request could not be processed.",
        "request.not_found": "The requested resource was not found.",
        "task.max_attempts": "The conversion exceeded the maximum number of attempts.",
        "task.invalid_source": "The source file is not valid.",
        "task.missing_source": "The source file was not found.",
        "task.generic_failure": "The file could not be converted.",
        "service.unsupported": "This format combination is not supported.",
        "service.pandoc_missing": "Pandoc is not installed or could not be found in PATH.",
        "service.pandoc_failed": "Pandoc could not convert the document.",
        "service.libreoffice_missing": "LibreOffice is not installed or could not be found in PATH. On WSL/Ubuntu, run: sudo apt install libreoffice-writer",
        "service.pdf_timeout": "The PDF conversion exceeded the 120-second time limit.",
        "service.libreoffice_failed": "LibreOffice could not convert the document to PDF.{detail}",
        "service.pdf_not_generated": "The PDF file was not generated.",
        "service.pdf2docx_missing": "The pdf2docx dependency is not installed. Run: python -m pip install -r requirements.txt",
        "service.pdf_to_docx_failed": "The PDF could not be converted to DOCX. Check that the file is valid and not protected.",
        "service.docx_not_generated": "The DOCX file was not generated.",
    },
    "es-419": {
        "validation.file_required": "Sube un archivo para convertir.",
        "validation.output_required": "Elige un formato de salida.",
        "validation.output_invalid": "El formato de salida seleccionado no es válido.",
        "validation.file_type": "Solo se aceptan archivos .docx y .pdf.",
        "validation.max_size": "El archivo debe tener un tamaño máximo de 10 MB.",
        "validation.invalid_pdf": "El contenido del archivo PDF no es válido.",
        "validation.invalid_docx": "El contenido del archivo DOCX no es válido.",
        "validation.pdf_output": "Los archivos PDF solo se pueden convertir a DOCX.",
        "validation.docx_output": "Los archivos DOCX se pueden convertir a Markdown, HTML o PDF.",
        "validation.invalid_data": "Datos no válidos.",
        "queue.unavailable": "El servicio de conversión no está disponible temporalmente.",
        "request.failed": "No se pudo procesar la solicitud.",
        "request.not_found": "No se encontró el recurso solicitado.",
        "task.max_attempts": "La conversión superó el número máximo de intentos.",
        "task.invalid_source": "El archivo de origen no es válido.",
        "task.missing_source": "No se encontró el archivo de origen.",
        "task.generic_failure": "No se pudo convertir el archivo.",
        "service.unsupported": "Esta combinación de formatos no es compatible.",
        "service.pandoc_missing": "Pandoc no está instalado o no se encontró en PATH.",
        "service.pandoc_failed": "Pandoc no pudo convertir el documento.",
        "service.libreoffice_missing": "LibreOffice no está instalado o no se encontró en PATH. En WSL/Ubuntu, ejecuta: sudo apt install libreoffice-writer",
        "service.pdf_timeout": "La conversión a PDF superó el límite de 120 segundos.",
        "service.libreoffice_failed": "LibreOffice no pudo convertir el documento a PDF.{detail}",
        "service.pdf_not_generated": "No se generó el archivo PDF.",
        "service.pdf2docx_missing": "La dependencia pdf2docx no está instalada. Ejecuta: python -m pip install -r requirements.txt",
        "service.pdf_to_docx_failed": "No se pudo convertir el PDF a DOCX. Verifica que el archivo sea válido y no esté protegido.",
        "service.docx_not_generated": "No se generó el archivo DOCX.",
    },
}


def normalize_language(value: str | None) -> str:
    language = (value or "").strip().lower().replace("_", "-")
    if language.startswith("en"):
        return "en"
    if language.startswith("es"):
        return "es-419"
    return DEFAULT_LANGUAGE


def language_from_header(value: str | None) -> str:
    if not value:
        return DEFAULT_LANGUAGE

    candidates: list[tuple[float, int, str]] = []
    for index, item in enumerate(value.split(",")):
        parts = [part.strip() for part in item.split(";")]
        quality = 1.0
        for parameter in parts[1:]:
            if parameter.startswith("q="):
                try:
                    quality = float(parameter[2:])
                except ValueError:
                    quality = 0.0
        candidates.append((quality, -index, parts[0]))

    for _quality, _index, language in sorted(candidates, reverse=True):
        if language.lower().startswith(("pt", "en", "es")):
            return normalize_language(language)
    return DEFAULT_LANGUAGE


def request_language(request: Any) -> str:
    if request is None:
        return DEFAULT_LANGUAGE
    return language_from_header(request.headers.get("Accept-Language"))


def translate(key: str, language: str | None = None, **params: Any) -> str:
    locale = normalize_language(language)
    template = MESSAGES.get(locale, MESSAGES[DEFAULT_LANGUAGE]).get(
        key, MESSAGES[DEFAULT_LANGUAGE].get(key, key)
    )
    return template.format(**params)


def localized_exception_message(exc: Exception, language: str) -> str:
    message_code = getattr(exc, "message_code", None)
    if not message_code:
        return str(exc)
    params = getattr(exc, "message_params", {})
    return translate(message_code, language, **params)
