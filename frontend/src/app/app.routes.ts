import { Routes } from '@angular/router';

import { DownloadPageComponent } from './pages/download/download-page.component';
import { HomePageComponent } from './pages/home/home-page.component';
import { LoadingPageComponent } from './pages/loading/loading-page.component';

export const routes: Routes = [
  { path: '', component: HomePageComponent },
  {
    path: 'conversoes/:id/processando',
    component: LoadingPageComponent,
  },
  {
    path: 'conversoes/:id/download',
    component: DownloadPageComponent,
  },
  { path: '**', redirectTo: '' },
];
