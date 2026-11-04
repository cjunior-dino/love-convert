import { DOCUMENT } from '@angular/common';
import { Injectable, inject, signal } from '@angular/core';

import {
  LANGUAGE_OPTIONS,
  SupportedLocale,
  TRANSLATIONS,
} from './translations';

const STORAGE_KEY = 'loveconvert:language';

export function normalizeLocale(value: string | null | undefined): SupportedLocale {
  const language = (value ?? '').toLowerCase().replace('_', '-');
  if (language.startsWith('en')) {
    return 'en';
  }
  if (language.startsWith('es')) {
    return 'es-419';
  }
  return 'pt-BR';
}

@Injectable({ providedIn: 'root' })
export class LanguageService {
  private readonly document = inject(DOCUMENT);
  private readonly localeState = signal<SupportedLocale>(this.initialLocale());

  readonly locale = this.localeState.asReadonly();
  readonly options = LANGUAGE_OPTIONS;

  constructor() {
    this.applyDocumentLanguage(this.localeState());
  }

  setLocale(locale: SupportedLocale): void {
    this.localeState.set(locale);
    this.applyDocumentLanguage(locale);
    try {
      localStorage.setItem(STORAGE_KEY, locale);
    } catch {
      // O idioma continua ativo durante a sessão quando o storage não está disponível.
    }
  }

  t(key: string, params: Record<string, string | number> = {}): string {
    const catalog = TRANSLATIONS[this.localeState()];
    let message = catalog[key] ?? TRANSLATIONS['pt-BR'][key] ?? key;
    for (const [name, value] of Object.entries(params)) {
      message = message.replaceAll(`{${name}}`, String(value));
    }
    return message;
  }

  private initialLocale(): SupportedLocale {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved === 'pt-BR' || saved === 'en' || saved === 'es-419') {
        return saved;
      }
    } catch {
      // A detecção do navegador continua disponível sem localStorage.
    }

    const browserLanguages = navigator.languages?.length
      ? navigator.languages
      : [navigator.language];
    const preferred = browserLanguages.find((language) =>
      /^(pt|en|es)(-|$)/i.test(language),
    );
    return normalizeLocale(preferred);
  }

  private applyDocumentLanguage(locale: SupportedLocale): void {
    this.document.documentElement.lang = locale;
  }
}
