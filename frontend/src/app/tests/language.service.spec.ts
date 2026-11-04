import { TestBed } from '@angular/core/testing';

import {
  LanguageService,
  normalizeLocale,
} from '../core/i18n/language.service';

describe('LanguageService', () => {
  beforeEach(() => {
    localStorage.clear();
    TestBed.configureTestingModule({});
  });

  it('mapeia idiomas do navegador para as localidades suportadas', () => {
    expect(normalizeLocale('pt-BR')).toBe('pt-BR');
    expect(normalizeLocale('en-US')).toBe('en');
    expect(normalizeLocale('es-MX')).toBe('es-419');
    expect(normalizeLocale('fr-FR')).toBe('pt-BR');
  });

  it('usa o idioma compatível preferido pelo navegador na primeira visita', () => {
    const languages = vi
      .spyOn(window.navigator, 'languages', 'get')
      .mockReturnValue(['es-MX', 'en-US']);

    const service = TestBed.inject(LanguageService);
    expect(service.locale()).toBe('es-419');
    languages.mockRestore();
  });

  it('salva a escolha e atualiza o idioma do documento', () => {
    const service = TestBed.inject(LanguageService);
    service.setLocale('es-419');

    expect(service.locale()).toBe('es-419');
    expect(localStorage.getItem('loveconvert:language')).toBe('es-419');
    expect(document.documentElement.lang).toBe('es-419');
    expect(service.t('nav.privacy')).toBe('Privacidad');
  });
});
