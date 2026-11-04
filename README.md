# LoveConvert

Aplicação web para converter documentos DOCX em PDF, HTML ou Markdown e arquivos PDF em DOCX. As conversões são processadas em segundo plano por Celery, com Redis como fila e PostgreSQL como banco de dados.

O fluxo da interface possui três páginas:

1. envio do arquivo e escolha do formato;
2. acompanhamento do processamento;
3. download, com uma tentativa automática e botão manual como alternativa.

## Idiomas

A interface e as mensagens da API estão disponíveis em:

- português do Brasil (`pt-BR`);
- inglês (`en`);
- espanhol latino-americano (`es-419`).

Na primeira visita, o frontend escolhe o idioma a partir das preferências do navegador. O seletor no cabeçalho permite trocar o idioma a qualquer momento e salva a escolha no `localStorage`. As requisições enviam `Accept-Language` ao Django, e o idioma da conversão é armazenado para que mensagens assíncronas do worker Celery sejam produzidas no mesmo idioma.

A conversão de PDF para Word é feita **sem OCR**. PDFs compostos somente por imagens podem gerar um DOCX sem texto editável.

## Arquitetura

```text
Caddy
  └── Frontend Angular / Nginx
        └── Backend Django / Gunicorn
              ├── PostgreSQL: metadados e status
              ├── Redis: fila de identificadores
              └── Celery Worker: conversões

Celery Beat
  └── limpeza periódica de arquivos expirados
```

Os arquivos não passam pelo Redis. O backend salva o upload no volume `conversion_files`, envia somente o UUID ao Redis e o worker usa o UUID para localizar o registro e o arquivo.

## Formatos disponíveis

| Entrada | Saída | Ferramenta |
|---|---|---|
| DOCX | PDF | LibreOffice Writer headless |
| DOCX | HTML | Pandoc |
| DOCX | Markdown | Pandoc |
| PDF | DOCX sem OCR | pdf2docx |

O limite padrão de upload é 10 MB.

## Execução com Docker

### Pré-requisitos

- Docker Engine com Docker Compose;
- portas 80 e 443 disponíveis para implantação pública;
- DNS apontando para a VPS quando um domínio for utilizado.

Crie o arquivo local de configuração:

```bash
cp .env.example .env
```

Preencha pelo menos estas variáveis:

```env
APP_SITE=http://localhost
DJANGO_SECRET_KEY=troque-por-uma-chave-longa-e-aleatoria
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
DJANGO_CSRF_TRUSTED_ORIGINS=http://localhost
POSTGRES_DB=loveconvert
POSTGRES_USER=loveconvert
POSTGRES_PASSWORD=troque-por-uma-senha-longa-e-aleatoria
CONVERSION_RETENTION_MINUTES=60
```

Uma chave do Django pode ser gerada com:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(64))"
```

Inicie o ambiente:

```bash
docker compose up -d --build
docker compose ps
```

O Compose inicia:

- `postgres`: banco persistente;
- `redis`: fila interna sem porta pública;
- `migrate`: aplica migrations e encerra;
- `backend`: API Django;
- `worker`: Celery com uma conversão simultânea;
- `beat`: agenda a limpeza automática;
- `frontend`: Angular servido pelo Nginx;
- `caddy`: entrada HTTP/HTTPS.

Logs úteis:

```bash
docker compose logs -f backend worker beat
docker compose logs -f postgres redis
docker compose logs -f frontend caddy
```

Atualização após alterações:

```bash
docker compose up -d --build
```

Parar sem apagar dados:

```bash
docker compose down
```

O comando abaixo também remove PostgreSQL, arquivos temporários e dados do Caddy. Use somente quando esses dados puderem ser descartados:

```bash
docker compose down -v
```

## Volumes

- `postgres_data`: banco PostgreSQL;
- `conversion_files`: uploads e resultados temporários;
- `caddy_data`: certificados e dados do Caddy;
- `caddy_config`: configuração persistente do Caddy.

Backend, worker e beat compartilham apenas `conversion_files`. A pasta não é publicada diretamente pelo Nginx; o download passa por um endpoint que valida UUID, estado e caminho físico.

Por padrão, os documentos expiram após 60 minutos. A rotina periódica remove os arquivos e marca o registro como expirado.

## Desenvolvimento do frontend

```bash
cd frontend
npm install
npm start
```

O frontend fica em `http://localhost:4200` e encaminha `/api` para o backend conforme `proxy.conf.json`.

## Desenvolvimento do backend

O backend não possui fallback para SQLite. PostgreSQL e Redis precisam estar disponíveis.

Para executar somente PostgreSQL e Redis em contêineres, expondo-os exclusivamente no computador local:

```bash
docker compose -f docker-compose.yml -f docker-compose.local.yml up -d postgres redis
```

O arquivo `docker-compose.local.yml` publica PostgreSQL em `127.0.0.1:5432` e Redis em `127.0.0.1:6379`. Essas portas não são publicadas pela configuração de produção.

No WSL ou Ubuntu:

```bash
cd backend
python3 -m venv .venv-wsl
source .venv-wsl/bin/activate
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

Em outro terminal, inicie o worker:

```bash
cd backend
source .venv-wsl/bin/activate
celery -A config worker --loglevel=INFO --concurrency=1
```

Para a limpeza periódica:

```bash
cd backend
source .venv-wsl/bin/activate
celery -A config beat --loglevel=INFO
```

Variáveis usadas fora do Docker:

```env
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=loveconvert
POSTGRES_USER=loveconvert
POSTGRES_PASSWORD=sua-senha
CELERY_BROKER_URL=redis://localhost:6379/0
```

## Fluxo assíncrono

1. O frontend envia o arquivo.
2. Django valida extensão, assinatura e tamanho.
3. O upload é salvo com nome interno fixo em um diretório UUID.
4. PostgreSQL recebe um registro com status `pending`.
5. Redis recebe somente o UUID.
6. O worker atualiza o status para `processing` e converte.
7. O resultado é salvo no volume e o status muda para `completed` ou `failed`.
8. A página de processamento consulta o status e redireciona para download.

Uma tarefa pode ser retomada após a perda do worker. O número de inícios é limitado a três para impedir reenfileiramento infinito.

## API

### Criar conversão

```http
POST /api/conversions/
Content-Type: multipart/form-data
```

Campos:

- `file`: DOCX ou PDF;
- `output_format`: `pdf`, `html`, `markdown` ou `docx`, conforme a entrada.

O cabeçalho opcional `Accept-Language` aceita `pt-BR`, `en` e variantes de espanhol, normalizadas pelo backend para `es-419`.

Resposta `202 Accepted`:

```json
{
  "success": true,
  "conversion_id": "7f77efb7-8e55-45c1-a26f-fe2acf699fa4",
  "status": "pending",
  "status_url": "https://exemplo.com/api/conversions/7f77efb7-8e55-45c1-a26f-fe2acf699fa4/"
}
```

### Consultar status

```http
GET /api/conversions/{conversion_id}/
```

Quando concluída, a resposta inclui `download_url`. Para HTML e Markdown, inclui também `content`.

### Baixar resultado

```http
GET /api/conversions/download/{conversion_id}/{filename}
```

O download só é permitido para conversões concluídas e arquivos localizados no diretório esperado.

### Saúde

```http
GET /api/health/
```

Retorna `200` quando Django consegue consultar o PostgreSQL.

## Testes

### Backend com PostgreSQL

Com o ambiente Docker configurado:

```bash
docker compose up -d postgres redis
docker compose run --rm migrate
docker compose run --rm backend python manage.py test -v 2
docker compose run --rm backend python manage.py makemigrations --check --dry-run
```

Os testes ficam em:

- `backend/conversions/tests/`: API, conversores e tarefas Celery;
- `backend/tests/`: verificações gerais do projeto.

### Frontend

```bash
cd frontend
npm test
npm run build
```

Os testes ficam em `frontend/src/app/tests/` e cobrem seleção, aviso sem OCR, envio, rotas, polling, erros, download automático e botão manual.

## Fontes e fidelidade visual

A imagem inclui Liberation Sans, Liberation Serif, Carlito e Caladea como alternativas para Arial, Times New Roman, Calibri, Aptos e Cambria. Fontes licenciadas adicionais podem ser colocadas em `docker/fonts/` antes da construção.

A aparência do PDF depende das fontes e do mecanismo de renderização. O LibreOffice é utilizado para preservar o layout do DOCX com maior fidelidade no ambiente Linux.

## Estrutura principal

```text
backend/
├── config/
│   ├── celery.py
│   ├── health.py
│   └── settings.py
├── conversions/
│   ├── migrations/
│   ├── services/
│   ├── tests/
│   ├── models.py
│   ├── tasks.py
│   └── views.py
└── tests/

frontend/src/app/
├── core/
├── pages/
│   ├── home/
│   ├── loading/
│   └── download/
├── tests/
└── app.routes.ts
```

## Segurança operacional

- Redis e PostgreSQL não publicam portas para a internet.
- Os arquivos usam UUID e nomes internos controlados.
- O conteúdo básico de PDF e DOCX é validado antes do armazenamento.
- O worker executa uma conversão por vez e possui limites de tempo e memória.
- Credenciais ficam no `.env`, que não deve ser enviado ao repositório.
- O volume de conversões não deve ser incluído em backups permanentes.
