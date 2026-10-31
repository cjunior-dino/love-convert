import { CommonModule } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import {
  ChangeDetectionStrategy,
  ChangeDetectorRef,
  Component,
  inject,
} from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { Router } from '@angular/router';

import { OutputFormat } from '../../core/models/conversion.models';
import { ConversionService } from '../../core/services/conversion.service';
import { FileSelectionService } from '../../core/services/file-selection.service';

@Component({
  selector: 'app-home-page',
  standalone: true,
  imports: [CommonModule, MatButtonModule, MatProgressSpinnerModule],
  templateUrl: './home-page.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class HomePageComponent {
  private readonly conversionService = inject(ConversionService);
  private readonly fileSelection = inject(FileSelectionService);
  private readonly router = inject(Router);
  private readonly changeDetector = inject(ChangeDetectorRef);

  selectedFile: File | null = null;
  errorMessage = '';
  isLoading = false;
  isDragging = false;
  activeFormat: OutputFormat | null = null;

  readonly formatOptions: Record<
    OutputFormat,
    { description: string; action: string; shortLabel: string }
  > = {
    pdf: {
      description: 'Documento pronto para compartilhar',
      action: 'Converter para PDF',
      shortLabel: 'PDF',
    },
    html: {
      description: 'Página pronta para visualizar',
      action: 'Converter para HTML',
      shortLabel: 'HTML',
    },
    markdown: {
      description: 'Texto leve e estruturado',
      action: 'Converter para Markdown',
      shortLabel: 'MD',
    },
    docx: {
      description: 'Documento editável no Word, sem OCR',
      action: 'Converter para DOCX',
      shortLabel: 'DOCX',
    },
  };

  get isPdfInput(): boolean {
    return this.selectedFile?.name.toLowerCase().endsWith('.pdf') ?? false;
  }

  get selectedFileType(): string {
    return this.isPdfInput ? 'PDF' : 'DOCX';
  }

  get selectedFileSize(): string {
    return this.selectedFile
      ? this.fileSelection.formatSize(this.selectedFile.size)
      : '';
  }

  get availableFormats(): OutputFormat[] {
    return this.isPdfInput ? ['docx'] : ['pdf', 'html', 'markdown'];
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
    const validationError = this.fileSelection.validate(file);
    if (validationError) {
      this.selectedFile = null;
      this.errorMessage = validationError;
      this.changeDetector.markForCheck();
      return;
    }
    this.selectedFile = file;
    this.errorMessage = '';
    this.changeDetector.markForCheck();
  }

  selectOutputFormat(format: OutputFormat): void {
    if (!this.selectedFile || this.isLoading) {
      return;
    }

    this.isLoading = true;
    this.activeFormat = format;
    this.errorMessage = '';
    this.conversionService
      .enqueueConversion(this.selectedFile, format)
      .subscribe({
        next: (response) => {
          void this.router.navigate([
            '/conversoes',
            response.conversion_id,
            'processando',
          ]);
        },
        error: (error: HttpErrorResponse) => {
          this.errorMessage = this.readApiError(error);
          this.isLoading = false;
          this.activeFormat = null;
          this.changeDetector.markForCheck();
        },
      });
  }

  formatLabel(format: OutputFormat): string {
    const labels: Record<OutputFormat, string> = {
      markdown: 'Markdown',
      html: 'HTML',
      pdf: 'PDF',
      docx: 'Word',
    };
    return labels[format];
  }

  private readApiError(error: HttpErrorResponse): string {
    const body = error.error as { error?: unknown } | null;
    if (body && typeof body.error === 'string') {
      return body.error;
    }
    if (error.status === 0) {
      return 'Não foi possível conectar ao servidor.';
    }
    return 'Não foi possível iniciar a conversão. Tente novamente.';
  }
}
