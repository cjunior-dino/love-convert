import { DomSanitizer, SafeHtml } from '@angular/platform-browser';
import { inject, Injectable } from '@angular/core';
import DOMPurify from 'dompurify';
import { marked } from 'marked';

import { OutputFormat } from '../models/conversion.models';

@Injectable({ providedIn: 'root' })
export class PreviewService {
  private readonly sanitizer = inject(DomSanitizer);

  create(content: string, outputFormat: OutputFormat): SafeHtml {
    const html =
      outputFormat === 'markdown'
        ? (marked.parse(content, { async: false }) as string)
        : content;
    const cleanHtml = DOMPurify.sanitize(html, {
      USE_PROFILES: { html: true },
      FORBID_TAGS: ['script', 'style', 'object', 'embed'],
      FORBID_ATTR: ['srcdoc'],
    });
    return this.sanitizer.bypassSecurityTrustHtml(cleanHtml);
  }
}
