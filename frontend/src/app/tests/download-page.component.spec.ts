import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ActivatedRoute, convertToParamMap, Router } from '@angular/router';
import { of } from 'rxjs';

import { ConversionDetail } from '../core/models/conversion.models';
import { ConversionService } from '../core/services/conversion.service';
import { DownloadPageComponent } from '../pages/download/download-page.component';

const completed: ConversionDetail = {
  success: true,
  conversion_id: 'conversion-id',
  original_name: 'contrato.pdf',
  input_format: 'pdf',
  output_format: 'docx',
  status: 'completed',
  error: '',
  content: null,
  download_url: '/api/conversions/download/conversion-id/output.docx',
  expires_at: '2026-10-30T23:00:00Z',
};

describe('DownloadPageComponent', () => {
  let fixture: ComponentFixture<DownloadPageComponent>;
  let router: { navigate: ReturnType<typeof vi.fn>; navigateByUrl: ReturnType<typeof vi.fn> };
  let conversionService: {
    getConversion: ReturnType<typeof vi.fn>;
    absoluteDownloadUrl: ReturnType<typeof vi.fn>;
    downloadFile: ReturnType<typeof vi.fn>;
  };

  beforeEach(async () => {
    sessionStorage.clear();
    router = {
      navigate: vi.fn().mockResolvedValue(true),
      navigateByUrl: vi.fn().mockResolvedValue(true),
    };
    conversionService = {
      getConversion: vi.fn().mockReturnValue(of(completed)),
      absoluteDownloadUrl: vi.fn((path: string) => `http://localhost${path}`),
      downloadFile: vi
        .fn()
        .mockReturnValue(of(new Blob(['docx'], { type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' }))),
    };
    Object.defineProperty(window.URL, 'createObjectURL', {
      configurable: true,
      value: vi.fn().mockReturnValue('blob:http://localhost/download'),
    });
    Object.defineProperty(window.URL, 'revokeObjectURL', {
      configurable: true,
      value: vi.fn(),
    });
    await TestBed.configureTestingModule({
      imports: [DownloadPageComponent],
      providers: [
        {
          provide: ActivatedRoute,
          useValue: { snapshot: { paramMap: convertToParamMap({ id: 'conversion-id' }) } },
        },
        { provide: Router, useValue: router },
        { provide: ConversionService, useValue: conversionService },
      ],
    }).compileComponents();
    fixture = TestBed.createComponent(DownloadPageComponent);
  });

  it('exibe o botão manual de download', () => {
    fixture.detectChanges();
    const anchor = fixture.nativeElement.querySelector('.download-button') as HTMLAnchorElement;
    expect(anchor).not.toBeNull();
    expect(anchor.textContent).toContain('Baixar Word');
  });

  it('tenta baixar automaticamente apenas uma vez por sessão', () => {
    vi.useFakeTimers();
    const click = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => undefined);
    fixture.detectChanges();
    vi.advanceTimersByTime(300);

    expect(click).toHaveBeenCalledTimes(1);
    expect(conversionService.downloadFile).toHaveBeenCalledWith(
      'http://localhost/api/conversions/download/conversion-id/output.docx',
    );
    expect(sessionStorage.getItem('loveconvert:downloaded:conversion-id')).toBe('true');
    expect(fixture.componentInstance.automaticDownloadAttempted).toBe(true);
    click.mockRestore();
    vi.useRealTimers();
  });

  it('usa o nome original com a extensão de saída', () => {
    fixture.detectChanges();
    expect(fixture.componentInstance.downloadFilename).toBe('contrato.docx');
  });

  it('redireciona para processamento quando o arquivo ainda não terminou', () => {
    conversionService.getConversion.mockReturnValue(
      of({ ...completed, status: 'processing', download_url: null }),
    );
    fixture.detectChanges();
    expect(router.navigate).toHaveBeenCalledWith([
      '/conversoes',
      'conversion-id',
      'processando',
    ]);
  });
});
