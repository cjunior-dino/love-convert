# Contexto de continuidade do projeto Love Convert

Este documento reúne o histórico técnico, as decisões tomadas, o estado atual do projeto e os comandos necessários para continuar o desenvolvimento em outra máquina.

## Objetivo do projeto

O Love Convert é uma aplicação web para conversão local de documentos, composta por:

- frontend Angular;
- backend Django e Django REST Framework;
- conversão de DOCX para Markdown, HTML ou PDF;
- conversão de PDF para DOCX;
- download do arquivo convertido;
- armazenamento isolado de cada conversão em um diretório UUID.

## Histórico do problema

### Erro 503 inicial

A API retornava `503 Service Unavailable` ao converter documentos. A instalação feita com `pip install pandoc` adicionava apenas um pacote Python e não o executável oficial do Pandoc esperado pelo backend.

O Pandoc precisa estar instalado como programa do sistema e disponível no `PATH`.

### Conversão de DOCX para PDF com WeasyPrint

Uma versão intermediária utilizava o seguinte fluxo:

```text
DOCX -> Pandoc -> HTML -> WeasyPrint -> PDF
```

Esse fluxo alterava significativamente o documento:

- substituía fontes;
- ignorava algumas quebras de página;
- alterava margens e espaçamentos;
- reinterpretava partes do conteúdo como tabelas;
- mudava a distribuição do texto entre as páginas;
- produzia PDFs menores, mas com menor fidelidade visual.

Os PDFs dessa versão apresentavam os metadados:

```text
Creator: pandoc
Producer: WeasyPrint 70.0
```

### Popup de impressora no Windows

O uso do LibreOffice no Windows abriu uma janela relacionada à conexão com impressoras. Para evitar interface gráfica e permitir a implantação em VPS, a execução foi transferida para WSL, Linux ou contêiner Docker usando o modo headless.

### Decisão final para DOCX para PDF

A conversão passou a ser direta:

```text
DOCX -> LibreOffice Writer headless -> PDF
```

O comando equivalente é:

```bash
libreoffice --headless --convert-to pdf documento.docx
```

O backend utiliza um perfil isolado do LibreOffice para cada conversão, evitando conflitos entre processos e sem abrir janelas.

## Arquitetura de conversão atual

| Entrada | Saída | Conversor |
| --- | --- | --- |
| DOCX | Markdown | Pandoc |
| DOCX | HTML | Pandoc |
| DOCX | PDF | LibreOffice Writer headless |
| PDF | DOCX | pdf2docx |

## Principais alterações implementadas

### Backend

Arquivo principal:

```text
backend/conversions/services/document_converter.py
```

A conversão DOCX para PDF agora:

- procura `libreoffice` ou `soffice` no `PATH`;
- executa o processo sem shell e com lista de argumentos;
- utiliza `--headless`, `--nologo`, `--nodefault` e `--nofirststartwizard`;
- cria um perfil temporário isolado dentro do diretório da conversão;
- usa o filtro `pdf:writer_pdf_Export`;
- possui timeout de 120 segundos;
- remove o perfil temporário após a conversão;
- retorna mensagens específicas para dependência ausente, timeout e falha de conversão;
- salva o resultado final como `output.pdf`.

O WeasyPrint foi removido das dependências.

Foram adicionadas as dependências de produção:

```text
gunicorn
whitenoise
```

### Configuração Django

O arquivo `backend/config/settings.py` passou a aceitar variáveis de ambiente para:

- `DJANGO_SECRET_KEY`;
- `DJANGO_DEBUG`;
- `DJANGO_ALLOWED_HOSTS`;
- `DJANGO_CORS_ALLOWED_ORIGINS`;
- `DJANGO_CSRF_TRUSTED_ORIGINS`;
- `DJANGO_DB_PATH`;
- `DJANGO_MEDIA_ROOT`;
- `DJANGO_STATIC_ROOT`.

O WhiteNoise atende os arquivos estáticos do Django e o Gunicorn executa o backend no contêiner.

### Frontend

O frontend não utiliza mais uma URL fixa como `http://localhost:8000`.

As chamadas usam caminhos relativos:

```text
/api/conversions/
```

Em desenvolvimento, `frontend/proxy.conf.json` encaminha `/api` para `http://localhost:8000`.

Em produção, o Nginx encaminha `/api` para o serviço `backend:8000`.

## Ambiente Docker

Foi criado um único `Dockerfile` com dois alvos.

### Alvo backend

Contém:

- Python 3.12;
- Django;
- Gunicorn;
- LibreOffice Writer;
- Pandoc;
- pdf2docx;
- fontes alternativas compatíveis;
- usuário não privilegiado para execução;
- coleta de arquivos estáticos;
- migrações executadas ao iniciar o contêiner.

### Alvo frontend

Utiliza build em múltiplos estágios:

1. Node.js compila a aplicação Angular;
2. somente os arquivos estáticos finais são copiados para uma imagem Nginx.

As dependências de desenvolvimento do Node não permanecem na imagem final do frontend.

### Docker Compose

O `docker-compose.yml` inicia:

- `backend`: Django com Gunicorn e LibreOffice;
- `frontend`: Nginx com o build Angular;
- `caddy`: proxy público com HTTPS automático;
- volume `database_data`: banco SQLite persistente;
- volume `conversion_files`: entradas e saídas das conversões;
- healthcheck do backend antes do início do frontend.

Somente o Caddy publica as portas 80 e 443 no host. O frontend e o backend ficam acessíveis apenas pela rede interna do Compose.

## Arquivos adicionados para implantação

```text
Dockerfile
docker-compose.yml
.dockerignore
.env.example
docker/nginx.conf
docker/Caddyfile
docker/fontconfig-local.conf
docker/fonts/.gitkeep
frontend/proxy.conf.json
CONTINUIDADE.md
```

## Fontes e fidelidade dos PDFs

O documento utilizado nos testes declara principalmente a fonte `ArialMT`.

Quando a fonte não existe no Linux, o LibreOffice faz uma substituição. Essa substituição pode alterar:

- largura das linhas;
- quantidade de palavras por linha;
- altura das células de tabelas;
- quebras de página;
- quantidade total de páginas.

A imagem Docker inclui estas alternativas:

- Liberation Sans para Arial e ArialMT;
- Liberation Serif para Times New Roman;
- Carlito para Calibri e Aptos;
- Caladea para Cambria.

O mapeamento está em:

```text
docker/fontconfig-local.conf
```

Para máxima fidelidade, coloque arquivos de fontes devidamente licenciados em:

```text
docker/fonts/
```

Depois reconstrua as imagens:

```bash
docker compose up -d --build
```

Mesmo com as fontes corretas, versões diferentes do LibreOffice podem produzir pequenas diferenças de paginação. Para reprodução idêntica, fixe a versão do LibreOffice e use as mesmas fontes do ambiente que gerou o PDF de referência.

## Execução local no WSL

Partindo da raiz do projeto:

```bash
sudo apt update
sudo apt install -y python3-venv python3-pip pandoc \
  libreoffice-writer fonts-dejavu fonts-liberation2 fonts-crosextra-carlito
```

Para documentos que usam Arial e Times New Roman:

```bash
sudo apt install ttf-mscorefonts-installer
sudo fc-cache -f
```

O pacote pode solicitar a aceitação da licença das fontes.

Criação e ativação do ambiente Python:

```bash
cd backend
python3 -m venv ~/.venvs/love-convert
source ~/.venvs/love-convert/bin/activate
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

Em outro terminal:

```bash
cd frontend
npm install
npm start
```

Endereços locais:

- frontend: `http://localhost:4200`;
- backend: `http://localhost:8000/api/conversions/`.

## Implantação com Docker

### 1. Criar o arquivo de ambiente

Na raiz do projeto:

```bash
cp .env.example .env
```

Gere uma chave secreta:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(64))"
```

Exemplo de `.env`:

```env
APP_SITE=ilove-convert.online
DJANGO_SECRET_KEY=troque-por-uma-chave-longa-e-aleatoria
DJANGO_ALLOWED_HOSTS=ilove-convert.online
DJANGO_CSRF_TRUSTED_ORIGINS=https://ilove-convert.online
```

O registro DNS do domínio deve apontar para o IP da VPS. O Caddy obtém e renova o certificado TLS automaticamente.

### 2. Construir e iniciar

```bash
docker compose up -d --build
```

### 3. Conferir o estado

```bash
docker compose ps
docker compose logs -f backend
```

O backend deve aparecer como `healthy`.

### 4. Atualizar após mudanças

```bash
git pull
docker compose up -d --build
```

### 5. Parar sem apagar dados

```bash
docker compose down
```

Não use o comando abaixo sem intenção de apagar o banco e os arquivos convertidos:

```bash
docker compose down -v
```

## Validações realizadas

As seguintes verificações foram concluídas:

- 22 testes automatizados do backend aprovados;
- `python manage.py check` sem erros;
- nenhuma migração pendente;
- 9 testes automatizados do frontend aprovados;
- build Angular de produção aprovado;
- sintaxe e resolução do Docker Compose aprovadas;
- imagem Docker do backend construída;
- imagem Docker do frontend construída;
- backend iniciado e marcado como `healthy`;
- frontend iniciado depois do healthcheck;
- upload real de DOCX pela API realizado;
- download real do PDF realizado;
- PDF identificado como produzido por Writer e LibreOffice;
- PDF de teste gerado com 5 páginas;
- todas as páginas do PDF de teste inspecionadas visualmente.

Os contêineres utilizados na validação foram encerrados. As imagens Docker continuam disponíveis no Docker local. Os volumes nomeados foram preservados.

## Limitações e pontos de atenção

- As conversões são síncronas e ocupam a requisição até terminarem.
- O Gunicorn está configurado com timeout de 180 segundos.
- O SQLite é adequado para uma instalação pequena e com poucos acessos simultâneos.
- Os arquivos convertidos não possuem limpeza automática.
- A aplicação não possui autenticação.
- A aplicação deve ser publicada com HTTPS antes de ser exposta na internet.
- Conversões simultâneas consomem memória e CPU por causa do LibreOffice.
- Documentos com fontes ausentes podem apresentar diferenças visuais.
- A fidelidade exata depende da versão do LibreOffice e das fontes instaladas.
- O build do frontend informou vulnerabilidades em dependências do ambiente de compilação. A imagem final contém somente arquivos estáticos no Nginx, mas as dependências devem ser revisadas periodicamente com `npm audit`.

## Próximas melhorias recomendadas

1. Adicionar autenticação antes de disponibilizar a aplicação publicamente.
2. Criar rotina automática para apagar conversões antigas.
3. Limitar quantidade de conversões simultâneas.
4. Migrar para PostgreSQL se houver múltiplos usuários.
5. Adotar fila assíncrona para documentos grandes.
6. Adicionar endpoint específico de saúde HTTP.
7. Fixar versões de imagens e dependências para builds reprodutíveis.
8. Revisar as dependências do frontend indicadas pelo `npm audit`.
9. Adicionar testes ponta a ponta executados pelo pipeline do repositório.

## Arquivos mais importantes para continuar

```text
README.md
CONTINUIDADE.md
Dockerfile
docker-compose.yml
.env.example
backend/config/settings.py
backend/conversions/services/document_converter.py
backend/conversions/tests/test_document_converter.py
frontend/src/app/core/services/conversion.service.ts
frontend/proxy.conf.json
docker/nginx.conf
docker/Caddyfile
docker/fontconfig-local.conf
```

## Envio para o GitHub

Confira primeiro os arquivos:

```bash
git status
```

Adicione e registre as mudanças usando a identidade Git já configurada:

```bash
git add .
git commit -m "Configura conversão de documentos e ambiente Docker"
```

Se o repositório remoto ainda não estiver configurado:

```bash
git branch -M main
git remote add origin URL_DO_REPOSITORIO
git push -u origin main
```

Se o remoto já existir:

```bash
git push
```

O arquivo `.env` não deve ser enviado. Apenas `.env.example` deve permanecer no repositório.

## Como retomar em outra máquina

Na nova máquina:

```bash
git clone URL_DO_REPOSITORIO
cd love-convert
cp .env.example .env
```

Depois ajuste `.env` e escolha uma das opções:

```bash
docker compose up -d --build
```

ou siga a instalação manual descrita no `README.md` e na seção de execução local deste documento.

