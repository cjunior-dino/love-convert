import shutil
import subprocess
from pathlib import Path


class PandocNotFoundError(RuntimeError):
    pass


class PandocConversionError(RuntimeError):
    pass


class PandocConverter:
    TIMEOUT_SECONDS = 60

    @staticmethod
    def ensure_available():
        if shutil.which("pandoc") is None:
            raise PandocNotFoundError(
                "O Pandoc não está instalado ou não foi encontrado no PATH."
            )

    def convert(self, input_path: Path, output_format: str, output_dir: Path) -> Path:
        self.ensure_available()
        media_dir = output_dir / "media"
        media_dir.mkdir(parents=True, exist_ok=True)

        if output_format == "markdown":
            output_path = output_dir / "output.md"
            command = [
                "pandoc",
                str(input_path),
                "--from=docx",
                "--to=gfm",
                f"--extract-media={media_dir}",
                f"--output={output_path}",
            ]
        elif output_format == "html":
            output_path = output_dir / "output.html"
            command = [
                "pandoc",
                str(input_path),
                "--from=docx",
                "--to=html5",
                "--standalone",
                f"--extract-media={media_dir}",
                f"--output={output_path}",
            ]
        else:
            raise PandocConversionError("Formato de saída não suportado.")

        try:
            subprocess.run(
                command,
                check=True,
                capture_output=True,
                text=True,
                timeout=self.TIMEOUT_SECONDS,
            )
        except FileNotFoundError as exc:
            raise PandocNotFoundError(
                "O Pandoc não está instalado ou não foi encontrado no PATH."
            ) from exc
        except subprocess.TimeoutExpired as exc:
            raise PandocConversionError(
                "A conversão excedeu o tempo limite de 60 segundos."
            ) from exc
        except subprocess.CalledProcessError as exc:
            detail = (exc.stderr or "").strip()
            message = "O Pandoc não conseguiu converter o documento."
            if detail:
                message = f"{message} {detail[:300]}"
            raise PandocConversionError(message) from exc

        if not output_path.is_file():
            raise PandocConversionError("O arquivo convertido não foi gerado.")
        return output_path
