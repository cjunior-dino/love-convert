import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideNoopAnimations } from '@angular/platform-browser/animations';
import { ActivatedRoute, convertToParamMap, Router } from '@angular/router';
import { of } from 'rxjs';

import { ConversionDetail } from '../core/models/conversion.models';
import { ConversionService } from '../core/services/conversion.service';
import { LoadingPageComponent } from '../pages/loading/loading-page.component';

const processing: ConversionDetail = {
  success: true,
  conversion_id: 'conversion-id',
  original_name: 'contrato.pdf',
  input_format: 'pdf',
  output_format: 'docx',
  status: 'processing',
  error: '',
  content: null,
  download_url: null,
  expires_at: '2026-10-30T23:00:00Z',
};

describe('LoadingPageComponent', () => {
  let fixture: ComponentFixture<LoadingPageComponent>;
  let router: { navigate: ReturnType<typeof vi.fn>; navigateByUrl: ReturnType<typeof vi.fn> };
  let conversionService: { watchConversion: ReturnType<typeof vi.fn> };

  async function create(status: ConversionDetail = processing): Promise<void> {
    router = {
      navigate: vi.fn().mockResolvedValue(true),
      navigateByUrl: vi.fn().mockResolvedValue(true),
    };
    conversionService = { watchConversion: vi.fn().mockReturnValue(of(status)) };
    await TestBed.configureTestingModule({
      imports: [LoadingPageComponent],
      providers: [
        provideNoopAnimations(),
        {
          provide: ActivatedRoute,
          useValue: { snapshot: { paramMap: convertToParamMap({ id: 'conversion-id' }) } },
        },
        { provide: Router, useValue: router },
        { provide: ConversionService, useValue: conversionService },
      ],
    }).compileComponents();
    fixture = TestBed.createComponent(LoadingPageComponent);
    fixture.detectChanges();
  }

  afterEach(() => TestBed.resetTestingModule());

  it('mostra os formatos durante o processamento', async () => {
    await create();
    expect(fixture.nativeElement.textContent).toContain('Convertendo PDF para Word');
    expect(conversionService.watchConversion).toHaveBeenCalledWith('conversion-id');
  });

  it('redireciona para download quando a conversão termina', async () => {
    await create({
      ...processing,
      status: 'completed',
      download_url: '/api/conversions/download/conversion-id/output.docx',
    });
    expect(router.navigate).toHaveBeenCalledWith(
      ['/conversoes', 'conversion-id', 'download'],
      { replaceUrl: true },
    );
  });

  it('mostra o erro informado pelo backend', async () => {
    await create({ ...processing, status: 'failed', success: false, error: 'PDF inválido.' });
    expect(fixture.nativeElement.textContent).toContain('PDF inválido.');
  });
});
