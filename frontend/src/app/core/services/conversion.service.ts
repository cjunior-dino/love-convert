import { HttpClient } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { Observable, switchMap, takeWhile, timer } from 'rxjs';

import {
  ConversionDetail,
  ConversionQueuedResponse,
  OutputFormat,
} from '../models/conversion.models';

@Injectable({ providedIn: 'root' })
export class ConversionService {
  private readonly http = inject(HttpClient);
  private readonly apiBaseUrl = window.location.origin;

  enqueueConversion(
    file: File,
    outputFormat: OutputFormat,
  ): Observable<ConversionQueuedResponse> {
    const formData = new FormData();
    formData.append('file', file, file.name);
    formData.append('output_format', outputFormat);
    return this.http.post<ConversionQueuedResponse>(
      '/api/conversions/',
      formData,
    );
  }

  getConversion(conversionId: string): Observable<ConversionDetail> {
    return this.http.get<ConversionDetail>(
      `/api/conversions/${encodeURIComponent(conversionId)}/`,
    );
  }

  downloadFile(downloadUrl: string): Observable<Blob> {
    return this.http.get(downloadUrl, { responseType: 'blob' });
  }

  watchConversion(
    conversionId: string,
    intervalMs = 1500,
  ): Observable<ConversionDetail> {
    return timer(0, intervalMs).pipe(
      switchMap(() => this.getConversion(conversionId)),
      takeWhile(
        (conversion) =>
          conversion.status === 'pending' ||
          conversion.status === 'processing',
        true,
      ),
    );
  }

  absoluteDownloadUrl(downloadUrl: string): string {
    const parsedUrl = new URL(downloadUrl, this.apiBaseUrl);
    return new URL(
      `${parsedUrl.pathname}${parsedUrl.search}${parsedUrl.hash}`,
      this.apiBaseUrl,
    ).toString();
  }
}
