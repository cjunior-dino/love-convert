import { provideHttpClient } from '@angular/common/http';
import {
  HttpTestingController,
  provideHttpClientTesting,
} from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { ConversionService } from './conversion.service';

describe('ConversionService', () => {
  let service: ConversionService;
  let httpTesting: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(ConversionService);
    httpTesting = TestBed.inject(HttpTestingController);
  });

  afterEach(() => httpTesting.verify());

  it('envia o arquivo e o formato em FormData', () => {
    const file = new File(['docx'], 'documento.docx');

    service.convertDocument(file, 'markdown').subscribe();

    const request = httpTesting.expectOne('/api/conversions/');
    expect(request.request.method).toBe('POST');
    expect(request.request.body).toBeInstanceOf(FormData);
    const formData = request.request.body as FormData;
    expect((formData.get('file') as File).name).toBe('documento.docx');
    expect(formData.get('output_format')).toBe('markdown');
    request.flush({
      success: true,
      original_name: 'documento.docx',
      output_format: 'markdown',
      content: '# Documento',
      download_url: '/api/conversions/download/id/output.md',
    });
  });
});
