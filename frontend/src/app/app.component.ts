import {
  ChangeDetectionStrategy,
  Component,
  ViewEncapsulation,
  effect,
  inject,
} from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormsModule } from '@angular/forms';
import { Title } from '@angular/platform-browser';
import { NavigationEnd, Router, RouterLink, RouterOutlet } from '@angular/router';
import { filter } from 'rxjs';

import { LanguageService } from './core/i18n/language.service';
import { SupportedLocale } from './core/i18n/translations';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [FormsModule, RouterLink, RouterOutlet],
  templateUrl: './app.component.html',
  styleUrl: './app.component.scss',
  encapsulation: ViewEncapsulation.None,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class AppComponent {
  readonly i18n = inject(LanguageService);
  private readonly router = inject(Router);
  private readonly title = inject(Title);

  constructor() {
    this.router.events
      .pipe(
        filter((event): event is NavigationEnd => event instanceof NavigationEnd),
        takeUntilDestroyed(),
      )
      .subscribe(() => this.updateTitle());

    effect(() => {
      this.i18n.locale();
      this.updateTitle();
    });
  }

  setLanguage(locale: SupportedLocale): void {
    this.i18n.setLocale(locale);
  }

  private updateTitle(): void {
    const url = this.router.url;
    const key = url.includes('/download')
      ? 'title.download'
      : url.includes('/processando')
        ? 'title.loading'
        : 'title.home';
    this.title.setTitle(this.i18n.t(key));
  }
}
