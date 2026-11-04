import { HttpErrorResponse } from '@angular/common/http';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideNoopAnimations } from '@angular/platform-browser/animations';
import { Router } from '@angular/router';
import { of, throwError } from 'rxjs';

import { ConversionQueuedResponse } from '../core/models/conversion.models';
import { LanguageService } from '../core/i18n/language.service';
import { ConversionService } from '../core/services/conversion.service';
import { HomePageComponent } from '../pages/home/home-page.component';

const queued: ConversionQueuedResponse = {
  success: true,
  conversion_id: 'conversion-id',
  original_name: 'documento.pdf',
  input_format: 'pdf',
  output_format: 'docx',
  status: 'pending',
  error: '',
  content: null,
  download_url: null,
  expires_at: '2026-10-30T23:00:00Z',
  status_url: '/api/conversions/conversion-id/',
};

describe('HomePageComponent', () => {
  let fixture: ComponentFixture<HomePageComponent>;
  let component: HomePageComponent;
  let conversionService: { enqueueConversion: ReturnType<typeof vi.fn> };
  let router: { navigate: ReturnType<typeof vi.fn> };

  beforeEach(async () => {
    localStorage.setItem('loveconvert:language', 'pt-BR');
    conversionService = { enqueueConversion: vi.fn().mockReturnValue(of(queued)) };
    router = { navigate: vi.fn().mockResolvedValue(true) };

    await TestBed.configureTestingModule({
      imports: [HomePageComponent],
      providers: [
        provideNoopAnimations(),
        { provide: ConversionService, useValue: conversionService },
        { provide: Router, useValue: router },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(HomePageComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('exibe a área de envio inicialmente', () => {
    expect(fixture.nativeElement.textContent).toContain('Arraste seu documento aqui');
  });

  it('oferece somente Word e informa Sem OCR para PDF', () => {
    component.selectFile(new File(['pdf'], 'documento.pdf'));
    fixture.detectChanges();

    expect(component.availableFormats).toEqual(['docx']);
    expect(fixture.nativeElement.textContent).toContain('Sem OCR');
    expect(fixture.nativeElement.textContent).toContain('Documento editável no Word');
  });

  it('oferece PDF, HTML e Markdown para DOCX', () => {
    component.selectFile(new File(['docx'], 'documento.docx'));
    expect(component.availableFormats).toEqual(['pdf', 'html', 'markdown']);
  });

  it('atualiza os textos quando o idioma é alterado', () => {
    TestBed.inject(LanguageService).setLocale('es-419');
    fixture.detectChanges();

    expect(fixture.nativeElement.textContent).toContain(
      'Convierte cualquier documento',
    );
    expect(fixture.nativeElement.textContent).toContain(
      'Seleccionar archivo',
    );
  });

  it('envia a conversão e navega para a página de processamento', () => {
    const file = new File(['pdf'], 'documento.pdf');
    component.selectFile(file);
    component.selectOutputFormat('docx');

    expect(conversionService.enqueueConversion).toHaveBeenCalledWith(file, 'docx');
    expect(router.navigate).toHaveBeenCalledWith([
      '/conversoes',
      'conversion-id',
      'processando',
    ]);
  });

  it('mantém a página e mostra o erro quando o envio falha', () => {
    conversionService.enqueueConversion.mockReturnValue(
      throwError(
        () =>
          new HttpErrorResponse({
            status: 503,
            error: { error: 'Fila indisponível.' },
          }),
      ),
    );
    component.selectFile(new File(['docx'], 'documento.docx'));
    component.selectOutputFormat('pdf');
    fixture.detectChanges();

    expect(component.errorMessage).toBe('Fila indisponível.');
    expect(component.isLoading).toBe(false);
    expect(fixture.nativeElement.textContent).toContain('Fila indisponível.');
  });
});
