import { CommonModule } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { FormControl, FormGroup, ReactiveFormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatButtonToggleModule } from '@angular/material/button-toggle';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { MatTabsModule } from '@angular/material/tabs';
import { SafeHtml } from '@angular/platform-browser';

import {
  ConversionSuccessResponse,
  OutputFormat,
} from './core/models/conversion.models';
import { ConversionService } from './core/services/conversion.service';
import { FileSelectionService } from './core/services/file-selection.service';
import { PreviewService } from './core/services/preview.service';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    MatButtonModule,
    MatButtonToggleModule,
    MatProgressSpinnerModule,
    MatSnackBarModule,
    MatTabsModule,
  ],
  templateUrl: './app.component.html',
  styleUrl: './app.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class AppComponent {
  private readonly conversionService = inject(ConversionService);
  private readonly fileSelection = inject(FileSelectionService);
  private readonly previewService = inject(PreviewService);
  private readonly snackBar = inject(MatSnackBar);

  readonly form = new FormGroup({
    outputFormat: new FormControl<OutputFormat>('markdown', {
      nonNullable: true,
    }),
  });

  selectedFile: File | null = null;
  result: ConversionSuccessResponse | null = null;
  renderedPreview: SafeHtml | null = null;
  errorMessage = '';
  successMessage = '';
  isLoading = false;
  isDragging = false;

  get canConvert(): boolean {
    return this.selectedFile !== null && !this.isLoading;
  }

  get isPdfInput(): boolean {
    return this.selectedFile?.name.toLowerCase().endsWith('.pdf') ?? false;
  }

  get selectedFileType(): string {
    return this.isPdfInput ? 'PDF' : 'DOCX';
  }

  get isTextResult(): boolean {
    return (
      this.result?.output_format === 'markdown' ||
      this.result?.output_format === 'html'
    );
  }

  get selectedFileSize(): string {
    return this.selectedFile
      ? this.fileSelection.formatSize(this.selectedFile.size)
      : '';
  }

  get downloadUrl(): string {
    return this.result
      ? this.conversionService.absoluteDownloadUrl(this.result.download_url)
      : '';
  }

  onFileInput(event: Event): void {
    const input = event.target as HTMLInputElement;
    const file = input.files?.item(0);
    if (file) {
      this.selectFile(file);
    }
    input.value = '';
  }

  onDragOver(event: DragEvent): void {
    event.preventDefault();
    this.isDragging = true;
  }

  onDragLeave(event: DragEvent): void {
    event.preventDefault();
    this.isDragging = false;
  }

  onDrop(event: DragEvent): void {
    event.preventDefault();
    this.isDragging = false;
    const file = event.dataTransfer?.files.item(0);
    if (file) {
      this.selectFile(file);
    }
  }

  selectFile(file: File): void {
    this.clearResult();
    const validationError = this.fileSelection.validate(file);
    if (validationError) {
      this.selectedFile = null;
      this.errorMessage = validationError;
      return;
    }
    this.selectedFile = file;
    this.form.controls.outputFormat.setValue(
      file.name.toLowerCase().endsWith('.pdf') ? 'docx' : 'markdown',
    );
    this.errorMessage = '';
  }

  convert(): void {
    if (!this.selectedFile || this.isLoading) {
      return;
    }

    this.clearResult();
    this.isLoading = true;
    this.form.disable();
    const outputFormat = this.form.controls.outputFormat.getRawValue();

    this.conversionService
      .convertDocument(this.selectedFile, outputFormat)
      .subscribe({
        next: (response) => {
          this.result = response;
          this.renderedPreview =
            response.content !== null &&
            (response.output_format === 'markdown' ||
              response.output_format === 'html')
              ? this.previewService.create(
                  response.content,
                  response.output_format,
                )
              : null;
          this.successMessage = 'Conversão concluída. Seu arquivo está pronto.';
          this.finishLoading();
        },
        error: (error: HttpErrorResponse) => {
          this.errorMessage = this.readApiError(error);
          this.finishLoading();
        },
      });
  }

  async copyContent(): Promise<void> {
    if (!this.result?.content) {
      return;
    }
    try {
      await navigator.clipboard.writeText(this.result.content);
      this.snackBar.open('Conteúdo copiado.', 'Fechar', { duration: 2500 });
    } catch {
      this.snackBar.open('Não foi possível copiar o conteúdo.', 'Fechar', {
        duration: 3500,
      });
    }
  }

  newConversion(): void {
    this.selectedFile = null;
    this.form.reset({ outputFormat: 'markdown' });
    this.form.enable();
    this.clearResult();
  }

  formatLabel(format: OutputFormat): string {
    const labels: Record<OutputFormat, string> = {
      markdown: 'Markdown',
      html: 'HTML',
      pdf: 'PDF',
      docx: 'DOCX',
    };
    return labels[format];
  }

  private clearResult(): void {
    this.result = null;
    this.renderedPreview = null;
    this.errorMessage = '';
    this.successMessage = '';
  }

  private finishLoading(): void {
    this.isLoading = false;
    this.form.enable();
  }

  private readApiError(error: HttpErrorResponse): string {
    const body = error.error as { error?: unknown } | null;
    if (body && typeof body.error === 'string') {
      return body.error;
    }
    if (error.status === 0) {
      return 'Não foi possível conectar ao servidor local.';
    }
    return 'Não foi possível converter o arquivo. Tente novamente.';
  }
}
