import { CommonModule } from '@angular/common';
import {
  ChangeDetectionStrategy,
  ChangeDetectorRef,
  Component,
  DestroyRef,
  OnInit,
  inject,
} from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { MatButtonModule } from '@angular/material/button';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';

import { ConversionDetail } from '../../core/models/conversion.models';
import { ConversionService } from '../../core/services/conversion.service';

@Component({
  selector: 'app-loading-page',
  standalone: true,
  imports: [CommonModule, MatButtonModule, MatProgressSpinnerModule, RouterLink],
  templateUrl: './loading-page.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class LoadingPageComponent implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly conversionService = inject(ConversionService);
  private readonly destroyRef = inject(DestroyRef);
  private readonly changeDetector = inject(ChangeDetectorRef);

  conversion: ConversionDetail | null = null;
  errorMessage = '';

  ngOnInit(): void {
    const conversionId = this.route.snapshot.paramMap.get('id');
    if (!conversionId) {
      void this.router.navigateByUrl('/');
      return;
    }

    this.conversionService
      .watchConversion(conversionId)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (conversion) => {
          this.conversion = conversion;
          if (conversion.status === 'completed') {
            void this.router.navigate(
              ['/conversoes', conversionId, 'download'],
              { replaceUrl: true },
            );
            return;
          }
          if (conversion.status === 'failed') {
            this.errorMessage =
              conversion.error || 'Não foi possível concluir a conversão.';
          } else if (conversion.status === 'expired') {
            this.errorMessage = 'Esta conversão expirou. Envie o arquivo novamente.';
          }
          this.changeDetector.markForCheck();
        },
        error: () => {
          this.errorMessage = 'Não foi possível consultar o andamento da conversão.';
          this.changeDetector.markForCheck();
        },
      });
  }

  get progressTitle(): string {
    if (!this.conversion) {
      return 'Preparando sua conversão…';
    }
    return `Convertendo ${this.formatLabel(this.conversion.input_format)} para ${this.formatLabel(this.conversion.output_format)}…`;
  }

  private formatLabel(format: string): string {
    const labels: Record<string, string> = {
      docx: 'Word',
      pdf: 'PDF',
      html: 'HTML',
      markdown: 'Markdown',
    };
    return labels[format] ?? format.toUpperCase();
  }
}
