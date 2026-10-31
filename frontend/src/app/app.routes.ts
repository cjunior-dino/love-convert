import { Routes } from '@angular/router';

import { DownloadPageComponent } from './pages/download/download-page.component';
import { HomePageComponent } from './pages/home/home-page.component';
import { LoadingPageComponent } from './pages/loading/loading-page.component';

export const routes: Routes = [
  { path: '', component: HomePageComponent, title: 'LoveConvert' },
  {
    path: 'conversoes/:id/processando',
    component: LoadingPageComponent,
    title: 'Convertendo documento | LoveConvert',
  },
  {
    path: 'conversoes/:id/download',
    component: DownloadPageComponent,
    title: 'Baixar documento | LoveConvert',
  },
  { path: '**', redirectTo: '' },
];
