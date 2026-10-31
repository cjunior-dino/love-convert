import { provideHttpClient } from '@angular/common/http';
import {
  HttpTestingController,
  provideHttpClientTesting,
} from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { ConversionService } from '../core/services/conversion.service';

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
    service.enqueueConversion(file, 'pdf').subscribe();

    const request = httpTesting.expectOne('/api/conversions/');
    expect(request.request.method).toBe('POST');
    const formData = request.request.body as FormData;
    expect((formData.get('file') as File).name).toBe('documento.docx');
    expect(formData.get('output_format')).toBe('pdf');
    request.flush({});
  });

  it('consulta uma conversão pelo identificador', () => {
    service.getConversion('conversion-id').subscribe();
    const request = httpTesting.expectOne('/api/conversions/conversion-id/');
    expect(request.request.method).toBe('GET');
    request.flush({});
  });

  it('baixa o resultado como arquivo binário', () => {
    const url = 'http://localhost/api/conversions/download/id/output.pdf';
    let result: Blob | undefined;
    service.downloadFile(url).subscribe((file) => (result = file));

    const request = httpTesting.expectOne(url);
    expect(request.request.method).toBe('GET');
    expect(request.request.responseType).toBe('blob');
    request.flush(new Blob(['pdf'], { type: 'application/pdf' }));
    expect(result?.type).toBe('application/pdf');
  });

  it('repete a consulta até receber um estado final', () => {
    vi.useFakeTimers();
    const statuses: string[] = [];
    service
      .watchConversion('conversion-id', 1000)
      .subscribe((conversion) => statuses.push(conversion.status));

    vi.advanceTimersByTime(0);
    httpTesting.expectOne('/api/conversions/conversion-id/').flush({
      status: 'processing',
    });
    vi.advanceTimersByTime(1000);
    httpTesting.expectOne('/api/conversions/conversion-id/').flush({
      status: 'completed',
    });
    vi.advanceTimersByTime(3000);

    expect(statuses).toEqual(['processing', 'completed']);
    httpTesting.expectNone('/api/conversions/conversion-id/');
    vi.useRealTimers();
  });
});
