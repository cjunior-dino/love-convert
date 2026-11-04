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
import { LanguageService } from '../../core/i18n/language.service';
import { ConversionService } from '../../core/services/conversion.service';

@Component({
  selector: 'app-loading-page',
  standalone: true,
  imports: [CommonModule, MatButtonModule, MatProgressSpinnerModule, RouterLink],
  templateUrl: './loading-page.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class LoadingPageComponent implements OnInit {
  readonly i18n = inject(LanguageService);
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
              conversion.error || this.i18n.t('loading.genericError');
          } else if (conversion.status === 'expired') {
            this.errorMessage = this.i18n.t('loading.expired');
          }
          this.changeDetector.markForCheck();
        },
        error: () => {
          this.errorMessage = this.i18n.t('loading.statusError');
          this.changeDetector.markForCheck();
        },
      });
  }

  get progressTitle(): string {
    if (!this.conversion) {
      return this.i18n.t('loading.preparing');
    }
    return this.i18n.t('loading.converting', {
      input: this.formatLabel(this.conversion.input_format),
      output: this.formatLabel(this.conversion.output_format),
    });
  }

  private formatLabel(format: string): string {
    const labels: Record<string, string> = {
      docx: this.i18n.t('format.word'),
      pdf: 'PDF',
      html: 'HTML',
      markdown: 'Markdown',
    };
    return labels[format] ?? format.toUpperCase();
  }
}
