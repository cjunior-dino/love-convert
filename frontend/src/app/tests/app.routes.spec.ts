import { routes } from '../app.routes';

describe('Rotas da conversão', () => {
  it('possui páginas separadas para processamento e download', () => {
    expect(routes.some((route) => route.path === 'conversoes/:id/processando')).toBe(true);
    expect(routes.some((route) => route.path === 'conversoes/:id/download')).toBe(true);
  });
});
