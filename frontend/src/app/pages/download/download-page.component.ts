import { DOCUMENT } from '@angular/common';
import {
  ChangeDetectionStrategy,
  ChangeDetectorRef,
  Component,
  OnInit,
  inject,
} from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';

import { ConversionDetail } from '../../core/models/conversion.models';
import { ConversionService } from '../../core/services/conversion.service';

@Component({
  selector: 'app-download-page',
  standalone: true,
  imports: [MatButtonModule, RouterLink],
  templateUrl: './download-page.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class DownloadPageComponent implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly conversionService = inject(ConversionService);
  private readonly document = inject(DOCUMENT);
  private readonly changeDetector = inject(ChangeDetectorRef);

  conversion: ConversionDetail | null = null;
  errorMessage = '';
  downloadError = '';
  isDownloading = false;
  automaticDownloadAttempted = false;

  ngOnInit(): void {
    const conversionId = this.route.snapshot.paramMap.get('id');
    if (!conversionId) {
      void this.router.navigateByUrl('/');
      return;
    }

    this.conversionService.getConversion(conversionId).subscribe({
      next: (conversion) => {
        if (conversion.status === 'pending' || conversion.status === 'processing') {
          void this.router.navigate([
            '/conversoes',
            conversionId,
            'processando',
          ]);
          return;
        }
        if (conversion.status !== 'completed' || !conversion.download_url) {
          this.errorMessage =
            conversion.error || 'O arquivo não está mais disponível para download.';
          this.changeDetector.markForCheck();
          return;
        }

        this.conversion = conversion;
        this.changeDetector.markForCheck();
        if (!this.wasDownloaded(conversionId)) {
          setTimeout(() => this.triggerDownload(true), 300);
        }
      },
      error: () => {
        this.errorMessage = 'Não foi possível localizar esta conversão.';
        this.changeDetector.markForCheck();
      },
    });
  }

  get downloadUrl(): string {
    return this.conversion?.download_url
      ? this.conversionService.absoluteDownloadUrl(this.conversion.download_url)
      : '';
  }

  get outputLabel(): string {
    const labels: Record<string, string> = {
      docx: 'Word',
      pdf: 'PDF',
      html: 'HTML',
      markdown: 'Markdown',
    };
    return this.conversion ? labels[this.conversion.output_format] : '';
  }

  get downloadFilename(): string {
    if (!this.conversion) {
      return 'arquivo-convertido';
    }
    const extension = this.conversion.output_format === 'markdown'
      ? 'md'
      : this.conversion.output_format;
    const baseName = this.conversion.original_name.replace(/\.[^.]+$/, '');
    return `${baseName}.${extension}`;
  }

  triggerDownload(automatic = false): void {
    if (!this.downloadUrl || this.isDownloading) {
      return;
    }

    this.isDownloading = true;
    this.downloadError = '';
    this.changeDetector.markForCheck();

    this.conversionService.downloadFile(this.downloadUrl).subscribe({
      next: (file) => {
        this.saveFile(file);
        if (this.conversion) {
          this.rememberDownload(this.conversion.conversion_id);
        }
        this.isDownloading = false;
        this.automaticDownloadAttempted ||= automatic;
        this.changeDetector.markForCheck();
      },
      error: () => {
        this.isDownloading = false;
        this.automaticDownloadAttempted ||= automatic;
        this.downloadError =
          'O download automático foi bloqueado ou interrompido. Use o botão para tentar novamente.';
        this.changeDetector.markForCheck();
      },
    });
  }

  private saveFile(file: Blob): void {
    const browserUrl = this.document.defaultView?.URL;
    if (!browserUrl?.createObjectURL) {
      this.clickDownloadLink(this.downloadUrl);
      return;
    }

    const objectUrl = browserUrl.createObjectURL(file);
    this.clickDownloadLink(objectUrl);
    setTimeout(() => browserUrl.revokeObjectURL(objectUrl), 1000);
  }

  private clickDownloadLink(url: string): void {
    const anchor = this.document.createElement('a');
    anchor.href = url;
    anchor.download = this.downloadFilename;
    anchor.style.display = 'none';
    this.document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
  }

  private wasDownloaded(conversionId: string): boolean {
    try {
      return sessionStorage.getItem(this.storageKey(conversionId)) === 'true';
    } catch {
      return false;
    }
  }

  private rememberDownload(conversionId: string): void {
    try {
      sessionStorage.setItem(this.storageKey(conversionId), 'true');
    } catch {
      // O botão manual continua disponível quando o navegador bloqueia o storage.
    }
  }

  private storageKey(conversionId: string): string {
    return `loveconvert:downloaded:${conversionId}`;
  }
}
