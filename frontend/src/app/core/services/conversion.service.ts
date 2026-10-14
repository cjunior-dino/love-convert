import { HttpClient } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { Observable } from 'rxjs';

import {
  ConversionSuccessResponse,
  OutputFormat,
} from '../models/conversion.models';

@Injectable({ providedIn: 'root' })
export class ConversionService {
  private readonly http = inject(HttpClient);
  private readonly apiBaseUrl = window.location.origin;

  convertDocument(
    file: File,
    outputFormat: OutputFormat,
  ): Observable<ConversionSuccessResponse> {
    const formData = new FormData();
    formData.append('file', file, file.name);
    formData.append('output_format', outputFormat);
    return this.http.post<ConversionSuccessResponse>(
      '/api/conversions/',
      formData,
    );
  }

  absoluteDownloadUrl(downloadUrl: string): string {
    return new URL(downloadUrl, this.apiBaseUrl).toString();
  }
}
