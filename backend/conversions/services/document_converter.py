import shutil
import subprocess
from pathlib import Path

from .pandoc_converter import (
    PandocConversionError,
    PandocConverter,
    PandocNotFoundError,
)


class ConversionDependencyError(RuntimeError):
    pass


class DocumentConversionError(RuntimeError):
    pass


class DocumentConverter:
    PDF_TIMEOUT_SECONDS = 120

    def convert(self, input_path: Path, output_format: str, output_dir: Path) -> Path:
        input_format = input_path.suffix.lower().lstrip(".")

        if input_format == "docx" and output_format in {"markdown", "html"}:
            return self._convert_with_pandoc(input_path, output_format, output_dir)
        if input_format == "docx" and output_format == "pdf":
            return self._convert_docx_to_pdf(input_path, output_dir)
        if input_format == "pdf" and output_format == "docx":
            return self._convert_pdf_to_docx(input_path, output_dir)
        raise DocumentConversionError("Esta combinação de formatos não é suportada.")

    @staticmethod
    def _convert_with_pandoc(
        input_path: Path, output_format: str, output_dir: Path
    ) -> Path:
        try:
            return PandocConverter().convert(input_path, output_format, output_dir)
        except PandocNotFoundError as exc:
            raise ConversionDependencyError(str(exc)) from exc
        except PandocConversionError as exc:
            raise DocumentConversionError(str(exc)) from exc

    def _convert_docx_to_pdf(self, input_path: Path, output_dir: Path) -> Path:
        executable = shutil.which("libreoffice") or shutil.which("soffice")
        if executable is None:
            raise ConversionDependencyError(
                "O LibreOffice não está instalado ou não foi encontrado no PATH. "
                "No WSL/Ubuntu, execute: sudo apt install libreoffice-writer"
            )

        profile_dir = output_dir / ".libreoffice-profile"
        output_path = output_dir / "output.pdf"
        converted_path = output_dir / f"{input_path.stem}.pdf"
        profile_uri = profile_dir.resolve().as_uri()
        command = [
            executable,
            "--headless",
            "--nologo",
            "--nodefault",
            "--nofirststartwizard",
            f"-env:UserInstallation={profile_uri}",
            "--convert-to",
            "pdf:writer_pdf_Export",
            "--outdir",
            str(output_dir),
            str(input_path),
        ]

        try:
            subprocess.run(
                command,
                check=True,
                capture_output=True,
                text=True,
                timeout=self.PDF_TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired as exc:
            raise DocumentConversionError(
                "A conversão para PDF excedeu o tempo limite de 120 segundos."
            ) from exc
        except subprocess.CalledProcessError as exc:
            detail = (exc.stderr or exc.stdout or "").strip()
            message = "O LibreOffice não conseguiu converter o documento em PDF."
            if detail:
                message = f"{message} {detail[:300]}"
            raise DocumentConversionError(message) from exc
        finally:
            shutil.rmtree(profile_dir, ignore_errors=True)

        if not converted_path.is_file():
            raise DocumentConversionError("O arquivo PDF não foi gerado.")

        if converted_path != output_path:
            output_path.unlink(missing_ok=True)
            shutil.copy2(converted_path, output_path)
            converted_path.unlink()
        return output_path

    @staticmethod
    def _convert_pdf_to_docx(input_path: Path, output_dir: Path) -> Path:
        try:
            from pdf2docx import Converter
        except ImportError as exc:
            raise ConversionDependencyError(
                "A dependência pdf2docx não está instalada. "
                "Execute: python -m pip install -r requirements.txt"
            ) from exc

        output_path = output_dir / "output.docx"
        converter = None
        try:
            converter = Converter(str(input_path))
            converter.convert(str(output_path))
        except Exception as exc:
            raise DocumentConversionError(
                "Não foi possível converter o PDF em DOCX. "
                "Verifique se o arquivo é válido e não está protegido."
            ) from exc
        finally:
            if converter is not None:
                converter.close()

        if not output_path.is_file():
            raise DocumentConversionError("O arquivo DOCX não foi gerado.")
        return output_path

