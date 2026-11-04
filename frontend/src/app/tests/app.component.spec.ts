import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';

import { AppComponent } from '../app.component';
import { routes } from '../app.routes';
import { LanguageService } from '../core/i18n/language.service';

describe('AppComponent', () => {
  let fixture: ComponentFixture<AppComponent>;

  beforeEach(async () => {
    localStorage.setItem('loveconvert:language', 'pt-BR');
    await TestBed.configureTestingModule({
      imports: [AppComponent],
      providers: [provideRouter(routes)],
    }).compileComponents();
    fixture = TestBed.createComponent(AppComponent);
    fixture.detectChanges();
  });

  it('exibe o seletor com os três idiomas', () => {
    const options = fixture.nativeElement.querySelectorAll(
      '.language-selector option',
    );
    expect(options).toHaveLength(3);
  });

  it('troca o idioma da interface pelo seletor', () => {
    const select = fixture.nativeElement.querySelector(
      '.language-selector select',
    ) as HTMLSelectElement;
    select.value = 'en';
    select.dispatchEvent(new Event('change'));
    fixture.detectChanges();

    expect(TestBed.inject(LanguageService).locale()).toBe('en');
    expect(fixture.nativeElement.textContent).toContain('Privacy');
  });
});
