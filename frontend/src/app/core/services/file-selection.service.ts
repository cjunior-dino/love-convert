import { Injectable } from '@angular/core';

export const MAX_FILE_SIZE = 10 * 1024 * 1024;

@Injectable({ providedIn: 'root' })
export class FileSelectionService {
  validate(file: File): string | null {
    const extension = file.name.toLowerCase().split('.').pop();
    if (extension !== 'docx' && extension !== 'pdf') {
      return 'Selecione um arquivo com a extensão .docx ou .pdf.';
    }
    if (file.size > MAX_FILE_SIZE) {
      return 'O arquivo deve ter no máximo 10 MB.';
    }
    return null;
  }

  formatSize(bytes: number): string {
    if (bytes < 1024 * 1024) {
      return `${Math.max(1, Math.round(bytes / 1024))} KB`;
    }
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  }
}
