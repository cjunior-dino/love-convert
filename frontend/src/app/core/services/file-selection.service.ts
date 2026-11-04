import { Injectable, inject } from '@angular/core';

import { LanguageService } from '../i18n/language.service';

export const MAX_FILE_SIZE = 10 * 1024 * 1024;

@Injectable({ providedIn: 'root' })
export class FileSelectionService {
  private readonly i18n = inject(LanguageService);

  validate(file: File): string | null {
    const extension = file.name.toLowerCase().split('.').pop();
    if (extension !== 'docx' && extension !== 'pdf') {
      return this.i18n.t('error.invalidExtension');
    }
    if (file.size > MAX_FILE_SIZE) {
      return this.i18n.t('error.maxSize');
    }
    return null;
  }

  formatSize(bytes: number): string {
    if (bytes < 1024 * 1024) {
      return `${Math.max(1, Math.round(bytes / 1024))} KB`;
    }
    const size = new Intl.NumberFormat(this.i18n.locale(), {
      minimumFractionDigits: 1,
      maximumFractionDigits: 1,
    }).format(bytes / (1024 * 1024));
    return `${size} MB`;
  }
}
