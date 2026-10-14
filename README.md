# Love Convert

Aplicação full stack local para converter documentos `.docx` em Markdown (GFM), HTML ou PDF e arquivos `.pdf` em DOCX. O frontend Angular oferece upload por clique ou arrastar e soltar, validação, progresso, prévia segura para formatos de texto e download. O backend Django executa as conversões de forma síncrona, registra o estado no SQLite e isola cada conversão em um diretório UUID.

## Pré-requisitos

- Windows 10 ou 11 com PowerShell, WSL 2 ou Linux;
- Python 3.10 ou superior;
- Node.js 22 LTS ou superior e npm;
- Pandoc disponível no `PATH`;
- LibreOffice Writer disponível no `PATH` para DOCX → PDF.

Para executar todas as conversões, prefira iniciar o backend pelo WSL/Linux. O LibreOffice é chamado em modo headless, sem abrir janelas ou acessar a interface de impressão.

Confirme as instalações:

```powershell
python --version
node --version
npm.cmd --version
pandoc --version
libreoffice --version
```

Se o Python ainda não estiver instalado:

```powershell
winget install --id Python.Python.3.12
```

Feche e reabra o PowerShell depois de instalar programas com o `winget`.

## Instalação do backend

Partindo da raiz do projeto:

```powershell
cd backend

python -m venv .venv

.\.venv\Scripts\Activate.ps1

python -m pip install -r requirements.txt

python manage.py migrate

python manage.py runserver
```

Se a política do PowerShell impedir a ativação do ambiente virtual, use os executáveis diretamente:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py runserver
```

O backend ficará disponível em [http://localhost:8000/api/conversions/](http://localhost:8000/api/conversions/).

### Backend no WSL ou Ubuntu

No Ubuntu/WSL, instale primeiro as dependências do sistema:

```bash
sudo apt update
sudo apt install -y python3-venv python3-pip pandoc \
  libreoffice-writer fonts-dejavu fonts-liberation2 fonts-crosextra-carlito
```

O LibreOffice usa as fontes instaladas no servidor. Se os documentos utilizarem Arial, Times New Roman ou outras fontes Microsoft, instale também o pacote abaixo para evitar alterações nas quebras de linha e na quantidade de páginas:

```bash
sudo apt install ttf-mscorefonts-installer
sudo fc-cache -f
```

Esse pacote pode solicitar a aceitação da licença das fontes durante a instalação.

Depois, partindo da raiz do projeto:

```bash
cd backend
python3 -m venv ~/.venvs/love-convert
source ~/.venvs/love-convert/bin/activate
python -m pip install -r requirements.txt
libreoffice --version
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

## Instalação do Pandoc

```powershell
winget install --id JohnMacFarlane.Pandoc
```

Abra um novo PowerShell e verifique:

```powershell
pandoc --version
```

Sem o Pandoc, o servidor inicia normalmente, mas conversões retornam uma mensagem clara informando que o executável não foi encontrado.

## Conversores

A conversão de DOCX para PDF usa diretamente o LibreOffice Writer em modo headless. Markdown e HTML usam Pandoc. A conversão de PDF para DOCX usa `pdf2docx`, instalado automaticamente com `requirements.txt`.

## Execução com Docker

O `Dockerfile` possui dois alvos: `backend`, com Django, Gunicorn, Pandoc e LibreOffice, e `frontend`, com o build Angular servido pelo Nginx. O `docker-compose.yml` conecta os serviços, executa as migrações, mantém o banco e os arquivos convertidos em volumes persistentes e usa Caddy como entrada pública com HTTPS automático.

Na raiz do projeto, crie a configuração local:

```bash
cp .env.example .env
```

Gere uma chave e coloque o valor em `DJANGO_SECRET_KEY` dentro do arquivo `.env`:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(64))"
```

No mesmo arquivo, substitua `seu-dominio.com` pelo domínio ou endereço IP da VPS. Para uma instalação apenas local, mantenha `APP_SITE=http://localhost` e `localhost,127.0.0.1` nos hosts permitidos.

Exemplo para produção em `ilove-convert.online`:

```env
APP_SITE=ilove-convert.online
DJANGO_SECRET_KEY=troque-por-uma-chave-longa-e-aleatoria
DJANGO_ALLOWED_HOSTS=ilove-convert.online
DJANGO_CSRF_TRUSTED_ORIGINS=https://ilove-convert.online
```

O DNS do domínio deve apontar para o IP público da VPS e as portas TCP 80 e 443 e UDP 443 precisam estar liberadas. O Caddy obtém e renova o certificado TLS automaticamente.

Construa e inicie os contêineres:

```bash
docker compose build
docker compose up -d
docker compose ps
```

A aplicação ficará disponível no endereço definido por `APP_SITE`. Para acompanhar o backend e o proxy HTTPS:

```bash
docker compose logs -f backend
docker compose logs -f caddy
```

Depois de alterar o código, atualize o ambiente com:

```bash
docker compose up -d --build
```

Para interromper os serviços sem apagar os documentos e o banco:

```bash
docker compose down
```

Os volumes `database_data`, `conversion_files`, `caddy_data` e `caddy_config` são mantidos pelo Docker. O comando `docker compose down -v` também apaga esses volumes e deve ser usado apenas quando os dados não forem mais necessários.

### Fontes no contêiner

A imagem inclui Liberation Sans, Liberation Serif, Carlito e Caladea como alternativas métricas para Arial, Times New Roman, Calibri, Aptos e Cambria. Para máxima fidelidade, coloque arquivos de fontes devidamente licenciados em `docker/fonts/` antes de construir a imagem e execute novamente `docker compose up -d --build`.

## Instalação do frontend

Em outro PowerShell, partindo da raiz do projeto:

```powershell
cd frontend

npm.cmd install

npm.cmd start
```

O frontend ficará disponível em [http://localhost:4200](http://localhost:4200). O CORS do backend aceita essa origem local.

## Como usar

1. Inicie o backend e o frontend em dois terminais.
2. Abra `http://localhost:4200`.
3. Arraste um arquivo `.docx` ou `.pdf` para a área indicada ou clique em **Selecionar arquivo**.
4. Para DOCX, escolha **Markdown**, **HTML** ou **PDF**. Para PDF, a saída DOCX é selecionada automaticamente.
5. Clique em **Converter documento**.
6. Confira o código ou a visualização renderizada, copie o conteúdo ou baixe o resultado.
7. Clique em **Nova conversão** para recomeçar.

O arquivo deve ter no máximo 10 MB. A prévia renderizada é sanitizada com DOMPurify e exibida em um `iframe` com sandbox.

## Teste manual da API

Com o backend em execução:

```powershell
$form = @{
  file = Get-Item -LiteralPath "C:\caminho\documento.docx"
  output_format = "markdown"
}

Invoke-RestMethod `
  -Uri "http://localhost:8000/api/conversions/" `
  -Method Post `
  -Form $form
```

Uma resposta bem-sucedida contém `content` e uma `download_url`. Em saídas PDF ou DOCX, `content` é `null` e o arquivo fica disponível pela URL de download.

## Testes automatizados

Backend:

```powershell
cd backend
.\.venv\Scripts\python.exe manage.py test -v 2
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
```

Os testes cobrem validações de arquivo e formato, limite de tamanho, Markdown, HTML, PDF, DOCX, dependências ausentes, falhas de conversão, download inexistente, path traversal, armazenamento seguro e CORS.

Frontend:

```powershell
cd frontend
npm.cmd test
npm.cmd run build
```

Os testes cobrem o estado inicial, botão desabilitado, seleção e rejeição de arquivo, `FormData`, resultado e erros da API.

## API

### `POST /api/conversions/`

Recebe `multipart/form-data`:

- `file`: arquivo `.docx` ou `.pdf`, obrigatório e limitado a 10 MB;
- `output_format`: `markdown`, `html` ou `pdf` para entrada DOCX; `docx` para entrada PDF.

Exemplo de sucesso (`201 Created`):

```json
{
  "success": true,
  "original_name": "documento.docx",
  "output_format": "markdown",
  "content": "# Conteúdo convertido",
  "download_url": "/api/conversions/download/8a62cdb0-3e87-4ef8-a192-b598a87c777b/output.md"
}
```

Erros de validação retornam `400`, erros de conversão retornam `422`, dependências ausentes retornam `503` e falhas inesperadas retornam `500`. A API nunca envia stack traces no corpo da resposta.

### `GET /api/conversions/download/{conversion_id}/{filename}`

Baixa apenas `output.md`, `output.html`, `output.pdf` ou `output.docx` associados a uma conversão concluída. UUID, nome fixo, diretório resolvido e existência do arquivo são validados antes do envio.

## Estrutura do projeto

```text
love-convert/
├── Dockerfile
├── docker-compose.yml
├── .dockerignore
├── .env.example
├── docker/
│   ├── nginx.conf
│   ├── fontconfig-local.conf
│   └── fonts/
├── backend/
│   ├── config/
│   │   ├── settings.py
│   │   ├── urls.py
│   │   ├── asgi.py
│   │   └── wsgi.py
│   ├── conversions/
│   │   ├── migrations/0001_initial.py
│   │   ├── services/pandoc_converter.py
│   │   ├── tests/
│   │   │   ├── test_api.py
│   │   │   └── test_pandoc_converter.py
│   │   ├── exceptions.py
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── urls.py
│   │   └── views.py
│   ├── manage.py
│   └── requirements.txt
├── frontend/
│   ├── public/favicon.svg
│   ├── src/
│   │   ├── app/
│   │   │   ├── core/
│   │   │   │   ├── models/conversion.models.ts
│   │   │   │   └── services/
│   │   │   │       ├── conversion.service.ts
│   │   │   │       ├── file-selection.service.ts
│   │   │   │       └── preview.service.ts
│   │   │   ├── app.component.html
│   │   │   ├── app.component.scss
│   │   │   ├── app.component.spec.ts
│   │   │   └── app.component.ts
│   │   ├── index.html
│   │   ├── main.ts
│   │   └── styles.scss
│   ├── angular.json
│   ├── package.json
│   ├── package-lock.json
│   ├── tsconfig.app.json
│   ├── tsconfig.json
│   └── tsconfig.spec.json
├── .gitignore
└── README.md
```

Durante o uso, o Django cria esta estrutura, ignorada pelo Git:

```text
backend/media/conversions/{uuid}/
├── input.docx ou input.pdf
├── output.md, output.html, output.pdf ou output.docx
└── media/
```

O nome original é mantido apenas como metadado. O armazenamento usa UUID e nomes internos fixos.

## Decisões técnicas

- Conversão síncrona por ser uma primeira versão local, sem a complexidade de filas.
- Serviço Pandoc separado da view, executado com lista de argumentos, `shell=False` implícito, timeout, captura de saída e verificação de retorno.
- PDF exportado diretamente pelo LibreOffice Writer em modo headless, com perfil isolado por conversão e sem interface gráfica.
- Imagem Docker separada em alvos de backend e frontend, com proxy reverso do Nginx e persistência em volumes nomeados.
- SQLite guarda status `pending`, `processing`, `completed` ou `failed`, além dos metadados e da mensagem de erro.
- Angular 21 standalone com Reactive Forms, HttpClient, Angular Material e tipagem discriminada das respostas.
- Sanitização explícita antes da prévia e isolamento adicional por `iframe sandbox`.
- URLs do backend centralizadas no serviço Angular para facilitar uma futura configuração por ambiente.

## Limitações desta versão

- O processamento é síncrono e ocupa a requisição até terminar.
- Os arquivos permanecem localmente até serem removidos manualmente.
- Não há autenticação, histórico na interface ou rotina automática de expiração.
- Em Markdown e HTML, imagens extraídas pelo Pandoc ficam no diretório `media/`, mas esta versão não oferece um pacote ZIP nem uma rota pública para elas. Na saída PDF, os recursos são incorporados antes da limpeza dos arquivos intermediários.
- A aplicação foi projetada para um único usuário local, não para exposição direta na internet.

## Melhorias futuras

- Limpeza automática de conversões antigas;
- download em ZIP com imagens e conteúdo;
- prévia de mídias extraídas;
- barra de progresso e cancelamento;
- configuração de URL da API por ambiente;
- fila assíncrona para conversões maiores;
- testes de ponta a ponta com navegador;
- endurecimento das configurações para uma implantação em rede.
