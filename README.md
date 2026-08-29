# Identidade Local — API

API REST do sistema educacional **Identidade Local**. Ela concentrará o
cadastro e a autenticação de usuários, o gerenciamento de sessões, a
persistência SQLite e a integração protegida com o ViaCEP.

## Estado atual

A estrutura inicial do serviço foi criada. A aplicação FastAPI, as rotas, a
persistência e os testes serão implementados progressivamente conforme o plano
do projeto.

## Estrutura

```text
app/
├── api/routes/   # endpoints HTTP
├── core/         # configurações, segurança e dependências
├── db/           # persistência e migrations
├── schemas/      # contratos Pydantic
└── services/     # regras de negócio e integrações
tests/            # testes automatizados
```

## Requisitos

- Python 3.14.3
- pip

## Configuração local

1. Crie e ative um ambiente virtual Python.
2. Instale as dependências com `pip install -r requirements.txt`.
3. Copie `.env.example` para `.env` e substitua `JWT_SECRET_KEY` por um segredo
   seguro.

Execute a aplicação localmente com `uvicorn app.main:app --reload`. As rotas e
as configurações completas serão implementadas nas próximas etapas.

## Docker

Construa a imagem no diretório deste repositório com:

```bash
docker build -t identidade-local-api .
```

Crie o arquivo `.env` a partir de `.env.example` e execute a imagem com:

```bash
docker run --rm --env-file .env -p 8000:8000 -v api_data:/data identidade-local-api
```

O serviço ficará disponível em `http://localhost:8000`. Para iniciar API e
interface juntas, consulte a seção Docker do repositório da interface.

## Variáveis de ambiente

| Variável | Descrição |
|---|---|
| `DATABASE_URL` | URL do banco SQLite. |
| `JWT_SECRET_KEY` | Segredo de assinatura dos tokens JWT. Não o versione. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Duração do token de acesso. |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Duração do token de renovação. |
| `CORS_ORIGINS` | Origens autorizadas para o client. |
| `VIACEP_BASE_URL` | URL base da integração ViaCEP. |
| `VIACEP_TIMEOUT_SECONDS` | Limite de tempo da chamada externa. |

## Licença

Projeto acadêmico.
