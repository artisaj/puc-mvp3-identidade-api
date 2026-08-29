# Identidade Local — API

API REST independente do sistema educacional **Identidade Local**. Centraliza
contas, credenciais, tokens, sessões, perfil e o acesso ao serviço público
ViaCEP. A interface React consome esta API; ela nunca se comunica diretamente
com o provedor externo.

## Arquitetura e segurança

O FastAPI organiza rotas HTTP, schemas Pydantic, serviços de domínio e
persistência SQLAlchemy/SQLite. Cada login cria uma sessão. A senha é guardada
somente como hash Argon2; o access token é um JWT de curta duração e o refresh
token opaco é guardado somente como hash. O refresh é enviado em cookie
`HttpOnly`, rotacionado a cada renovação e revogado no logout ou no encerramento
da sessão. A API aplica CORS para a origem configurada e protege perfil e
sessões com `Authorization: Bearer <access_token>`.

```text
React client ── REST JSON ──> FastAPI ──> SQLite
                                 │
                                 └── GET ──> ViaCEP
```

## Estrutura

```text
app/
├── api/routes/   # auth, users, sessions, addresses e health
├── core/         # configuração, JWT e dependências autenticadas
├── db/           # engine, modelos SQLAlchemy e migrations Alembic
├── schemas/      # contratos de entrada e saída
└── services/     # usuários, sessões e cliente ViaCEP
tests/            # testes automatizados de unidade e integração
```

## Instalação e execução local

Requer Python 3.14.3 e `pip`.

1. Crie e ative um ambiente virtual.
2. Instale as dependências: `pip install -r requirements.txt`.
3. Copie `.env.example` para `.env` e defina um valor forte, exclusivo e não
   versionado para `JWT_SECRET_KEY`.
4. Inicie: `uvicorn app.main:app --reload`.

A API fica em `http://localhost:8000`; a documentação interativa OpenAPI fica
em `http://localhost:8000/docs`. Para uma execução local persistente, mantenha
`DATABASE_URL=sqlite:////data/identidade_local.db` apenas quando `/data` existir
ou use uma URL SQLite para um arquivo local gravável.

## Dockerfile e Compose

O Dockerfile raiz instala as dependências em Python 3.14.3 e inicia Uvicorn na
porta 8000. Na raiz desta API, construa a imagem com
`docker build -t identidade-local-api .` e execute-a com
`docker run --rm --env-file .env -p 8000:8000 -v api_data:/data identidade-local-api`.
O volume nomeado preserva o SQLite em `/data`.

Para subir os dois componentes, mantenha os repositórios `api` e `client` lado
a lado, copie `.env.example` para `.env` nesta API e, na raiz do client, use
`docker compose up --build`. O Compose constrói esta API a partir de `../api`,
expõe a API em `http://localhost:8000`, o client em `http://localhost:5173` e
mantém o banco no volume `api_data`. Cada componente continua executável pelo
seu próprio Dockerfile, sem Compose.

## Variáveis de ambiente

| Variável | Obrigatória | Descrição e padrão de desenvolvimento |
|---|---:|---|
| `APP_NAME` | Não | Título da aplicação; padrão `Identidade Local API`. |
| `APP_ENV` | Não | Ambiente; `production` torna o cookie de refresh `Secure`. |
| `DATABASE_URL` | Sim | URL SQLite, como `sqlite:////data/identidade_local.db`. |
| `JWT_SECRET_KEY` | Sim | Segredo de assinatura JWT; use valor longo, aleatório e privado. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Não | Validade do access token; padrão `15`. |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Não | Validade do refresh token; padrão `7`. |
| `PASSWORD_RESET_TOKEN_EXPIRE_MINUTES` | Não | Validade do JWT de redefinição; padrão `15`. |
| `CORS_ORIGINS` | Não | Origens separadas por vírgula; padrão `http://localhost:5173`. |
| `VIACEP_BASE_URL` | Não | Base do ViaCEP; padrão `https://viacep.com.br/ws`. |
| `VIACEP_TIMEOUT_SECONDS` | Não | Timeout externo em segundos; padrão `3`. |
| `VIACEP_RATE_LIMIT_REQUESTS` | Não | Máximo de buscas por IP na janela; padrão `10`. |
| `VIACEP_RATE_LIMIT_WINDOW_SECONDS` | Não | Janela do limite em segundos; padrão `60`. |

Não versione `.env`, arquivos SQLite, tokens nem segredos.

## Rotas REST

Respostas e erros usam JSON; falhas são descritas em `detail`.

| Método e rota | Autenticação | Corpo / resultado | Códigos principais |
|---|---|---|---|
| `GET /health` | Não | Estado do serviço. | `200` |
| `POST /auth/register` | Não | Cria usuário com `name`, `email`, `password` e endereço opcional. | `201`, `409`, `422` |
| `POST /auth/login` | Não | Recebe `email` e `password`; retorna `access_token` e cria cookie `refresh_token`. | `200`, `401`, `422` |
| `POST /auth/refresh` | Cookie de refresh | Rotaciona o cookie e retorna novo `access_token`. | `200`, `401` |
| `POST /auth/logout` | Cookie de refresh | Revoga a sessão atual e remove o cookie. | `204` |
| `POST /auth/forgot-password` | Não | Aceita `email` sem confirmar a existência da conta. Só em desenvolvimento retorna `reset_token` temporário para uma conta ativa. | `202`, `422` |
| `POST /auth/reset-password` | JWT de reset | Aceita `token` e `new_password`, troca o hash Argon2 e revoga as sessões existentes. | `204`, `401`, `422` |
| `GET /addresses/lookup/{zip_code}` | Não | Retorna endereço normalizado para CEP de 8 dígitos. | `200`, `400`, `404`, `429`, `503` |
| `GET /users/me` | Bearer | Retorna o perfil autenticado, sem hash de senha. | `200`, `401` |
| `PUT /users/me` | Bearer | Atualiza `name` e/ou campos de endereço. | `200`, `401`, `422` |
| `GET /sessions` | Bearer | Lista sessões ativas do usuário atual. | `200`, `401` |
| `GET /sessions/{session_id}` | Bearer | Consulta uma sessão da própria conta. | `200`, `401`, `404` |
| `DELETE /sessions/{session_id}` | Bearer | Revoga uma sessão da própria conta. | `204`, `401`, `404` |

O `access_token` é retornado como `{"access_token": "...", "token_type":
"bearer"}` e deve ser enviado no cabeçalho Bearer. O refresh token nunca é
incluído no JSON. Uma sessão de outra conta é indistinguível de uma inexistente
e retorna `404`.

### Recuperação de senha em desenvolvimento

O fluxo sem e-mail existe somente para demonstração local. A solicitação em
`POST /auth/forgot-password` devolve sempre `{"accepted": true}` quando o
ambiente não é `development` ou a conta não existe, evitando enumeração de
e-mails. Em desenvolvimento, apenas para uma conta ativa, o campo
`reset_token` contém um JWT curto, assinado e com propósito exclusivo
`password_reset`.

`POST /auth/reset-password` valida assinatura, expiração, propósito e uma
impressão do hash de senha vigente. A nova senha recebe hash Argon2 e todas as
sessões de refresh anteriores são revogadas na mesma transação. A impressão faz
com que o token deixe de ser reutilizável após a primeira redefinição. Nunca
registre ou exponha esse token fora do ambiente de desenvolvimento.

## ViaCEP

A consulta pública é exposta em `GET /addresses/lookup/{zip_code}`; aceita
`01001000` ou `01001-000` e normaliza para campos como `street`, `city` e
`state`. A API é a única consumidora de
`https://viacep.com.br/ws/{cep}/json/`: o client usa exclusivamente a rota
interna acima. A integração não exige cadastro, chave ou token para a rota
utilizada.

Use-a apenas para a finalidade de preenchimento assistido de endereço, informe
um CEP brasileiro válido e respeite o limite simples por IP configurado. CEP
malformado retorna `400`, inexistente retorna `404`, excesso de consultas
retorna `429` e indisponibilidade, timeout, erro HTTP ou resposta inválida do
provedor retorna `503`. O usuário pode editar manualmente o endereço quando a
consulta não estiver disponível.

## Testes

Execute toda a suíte com `pytest`. Para executar exatamente no contêiner da API
sem instalar dependências locais, na raiz desta API use
`docker build -t identidade-local-api-test .` e
`docker run --rm -v "${PWD}/tests:/app/tests:ro" --entrypoint pytest identidade-local-api-test`.
No PowerShell, use `${PWD}\tests` no volume. A imagem de produção não inclui
os testes. Os testes
cobrem autenticação, expiração e revogação, acesso não autorizado, isolamento
de sessões, schemas, segurança e respostas do ViaCEP, incluindo falhas externas.

## Licença

Projeto acadêmico.
