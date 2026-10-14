import { HttpErrorResponse } from '@angular/common/http';
import { provideNoopAnimations } from '@angular/platform-browser/animations';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { Observable, of, throwError } from 'rxjs';

import { AppComponent } from './app.component';
import {
  ConversionSuccessResponse,
  OutputFormat,
} from './core/models/conversion.models';
import { ConversionService } from './core/services/conversion.service';

class ConversionServiceStub {
  response: Observable<ConversionSuccessResponse> = of({
    success: true,
    original_name: 'documento.docx',
    output_format: 'markdown',
    content: '# Conteúdo',
    download_url: '/api/conversions/download/id/output.md',
  });

  convertDocument(
    _file: File,
    _format: OutputFormat,
  ): Observable<ConversionSuccessResponse> {
    return this.response;
  }

  absoluteDownloadUrl(path: string): string {
    return `http://localhost:8000${path}`;
  }
}

describe('AppComponent', () => {
  let fixture: ComponentFixture<AppComponent>;
  let component: AppComponent;
  let conversionService: ConversionServiceStub;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AppComponent],
      providers: [
        provideNoopAnimations(),
        { provide: ConversionService, useClass: ConversionServiceStub },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(AppComponent);
    component = fixture.componentInstance;
    conversionService = TestBed.inject(
      ConversionService,
    ) as unknown as ConversionServiceStub;
    fixture.detectChanges();
  });

  it('inicia sem arquivo e com Markdown selecionado', () => {
    expect(component.selectedFile).toBeNull();
    expect(component.form.controls.outputFormat.value).toBe('markdown');
    expect(component.result).toBeNull();
  });

  it('mantém o botão desabilitado sem arquivo', () => {
    const button = fixture.nativeElement.querySelector(
      '[data-testid="convert-button"]',
    ) as HTMLButtonElement;
    expect(button.disabled).toBe(true);
  });

  it('aceita um arquivo DOCX válido', () => {
    const file = new File(['docx'], 'documento.docx');
    component.selectFile(file);
    expect(component.selectedFile).toBe(file);
    expect(component.errorMessage).toBe('');
    expect(component.canConvert).toBe(true);
  });

  it('aceita PDF e seleciona DOCX como saída', () => {
    const file = new File(['pdf'], 'documento.pdf');
    component.selectFile(file);
    expect(component.selectedFile).toBe(file);
    expect(component.form.controls.outputFormat.value).toBe('docx');
    expect(component.errorMessage).toBe('');
  });

  it('rejeita arquivo com extensão inválida', () => {
    component.selectFile(new File(['text'], 'documento.txt'));
    expect(component.selectedFile).toBeNull();
    expect(component.errorMessage).toContain('.docx');
    expect(component.errorMessage).toContain('.pdf');
  });

  it('exibe o resultado da conversão', () => {
    component.selectFile(new File(['docx'], 'documento.docx'));
    component.convert();
    fixture.detectChanges();
    expect(component.result?.content).toBe('# Conteúdo');
    expect(fixture.nativeElement.textContent).toContain('Documento convertido');
  });

  it('oculta a prévia para resultados binários', () => {
    conversionService.response = of({
      success: true,
      original_name: 'documento.docx',
      output_format: 'pdf',
      content: null,
      download_url: '/api/conversions/download/id/output.pdf',
    });
    component.selectFile(new File(['docx'], 'documento.docx'));
    component.form.controls.outputFormat.setValue('pdf');
    component.convert();
    fixture.detectChanges();

    expect(component.renderedPreview).toBeNull();
    expect(fixture.nativeElement.textContent).toContain(
      'prévia não está disponível',
    );
  });

  it('exibe erros retornados pela API', () => {
    conversionService.response = throwError(
      () =>
        new HttpErrorResponse({
          status: 422,
          error: { success: false, error: 'Documento corrompido.' },
        }),
    );
    component.selectFile(new File(['docx'], 'documento.docx'));
    component.convert();
    fixture.detectChanges();
    expect(component.errorMessage).toBe('Documento corrompido.');
    expect(fixture.nativeElement.textContent).toContain('Documento corrompido.');
  });
});
