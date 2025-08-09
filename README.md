# VidaPlus - Sistema de Gestão Hospitalar (2025)

Sistema de gestão hospitalar e de saúde consolidado em um único arquivo `vidaplus.py`, com API REST completa, autenticação JWT, auditoria, notificações e CRUD para Pacientes, Profissionais, Consultas e Receitas. Este README está atualizado para 2025 e reflete a arquitetura simplificada, o banco otimizado e a coleção Postman com 100% de aprovação.

### Destaques 2025
- Arquitetura simplificada: 1 arquivo Python (`vidaplus.py`) + 1 banco SQLite + 1 coleção Postman
- Endpoint para recriar o banco: `POST /api/recreate-db` (dev/test)
- Banco otimizado: apenas tabelas utilizadas
- Testes no Postman com scripts e variáveis automáticas (100% aprovado)

## Funcionalidades
- Autenticação JWT: login, perfil, logout
- Pacientes: CRUD com validação de CPF, e-mail e senha
- Profissionais: CRUD com validação de CRM/COREN e especialidades
- Consultas: CRUD com tipos Presencial/Telemedicina (campo `tipo`) e `link_telemedicina`
- Receitas (Prescrições): CRUD com `medicamentos`, `dosagem`, `duracao`, `observacoes`
- Auditoria: logging de ações críticas (tabela `auditoria`)
- Notificações: eventos do sistema (tabela `notificacoes`)
- Health check, informações do sistema e teste de CORS

## Tecnologias (2025)
- Python 3.10+
- Flask, Flask-SQLAlchemy, Flask-JWT-Extended, Flask-Bcrypt, Flask-CORS
- Banco: SQLite (arquivo `instance/vidaplus.db`)

## Instalação Rápida
1) Ambiente virtual
```bash
python -m venv venv
venv\Scripts\activate   # Windows
# source venv/bin/activate  # Linux/Mac
```
2) Dependências
```bash
pip install Flask Flask-SQLAlchemy Flask-JWT-Extended Flask-Bcrypt Flask-CORS
```
3) Iniciar API
```bash
python vidaplus.py
```
API disponível em `http://localhost:5000`.

## Estrutura (2025)
```
VidaPlus_Guilherme/
├── vidaplus.py                 # Aplicação Flask consolidada (modelos, rotas e utilitários)
├── README.md                   # Este documento
├── postman_vidaplus_final.json # Coleção Postman (100% aprovado)
└── instance/
    └── vidaplus.db            # Banco SQLite
```

## Endpoints Principais
- GET `/api/health` — Health check
- GET `/` — Informações do sistema
- GET `/api/test` — Teste de CORS
- POST `/api/recreate-db` — Recria o banco (dev/test)

### Autenticação (`/api/auth`)
- POST `/login`
- GET `/perfil`
- POST `/logout`

### Pacientes (`/api/pacientes`)
- POST `/` — criar
- GET `/` — listar
- GET `/<id>` — obter
- PUT `/<id>` — atualizar
- DELETE `/<id>` — excluir

### Profissionais (`/api/profissionais`)
- POST `/` — criar
- GET `/` — listar
- GET `/<id>` — obter
- PUT `/<id>` — atualizar
- DELETE `/<id>` — excluir

### Consultas (`/api/consultas`)
- POST `/` — criar (Presencial/Telemedicina)
- GET `/` — listar
- GET `/<id>` — obter
- PUT `/<id>` — atualizar
- DELETE `/<id>` — excluir

### Receitas/Prescrições (`/api/receitas`)
- POST `/` — criar
- GET `/` — listar
- GET `/<id>` — obter
- PUT `/<id>` — atualizar
- DELETE `/<id>` — excluir

## Banco de Dados (otimizado em 2025)
Tabelas mantidas: `usuarios`, `pacientes`, `profissionais`, `unidades`, `consultas`, `prescricoes`, `auditoria`, `notificacoes`.

Tabelas removidas (não utilizadas): `leitos`, `exames`, `prontuarios`, `telemedicina`.

Recriação rápida do banco (útil para testes):
```bash
curl -X POST http://localhost:5000/api/recreate-db
```

## Testes com Postman (100%)
1) Importe `postman_vidaplus_final.json` no Postman
2) Garanta que a variável `base_url = http://localhost:5000`
3) Execute os requests na ordem do grupo (a coleção já inclui o passo de recriar o banco e scripts que salvam token/IDs automaticamente)

## Exemplos Rápidos (cURL)
Login (retorna token JWT):
```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@vidaplus.com","senha":"admin123"}'
```

Criar paciente (exige Bearer token):
```bash
curl -X POST http://localhost:5000/api/pacientes \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <TOKEN>" \
  -d '{
    "email":"paciente1.teste@vidaplus.com",
    "senha":"Paciente123!",
    "cpf":"123.456.789-09",
    "nome":"João Silva",
    "data_nascimento":"1990-05-15",
    "sexo":"M"
  }'
```

## Segurança e Compliance
- JWT para autenticação e autorização
- Hash de senhas com bcrypt
- Auditoria de operações críticas
- Boas práticas LGPD (minimização, registro e segurança de dados)

## Deploy (2025)
Ambiente padrão de desenvolvimento: `python vidaplus.py`.

Para produção, recomenda-se um servidor WSGI (ex.: Gunicorn + proxy reverso):
```bash
gunicorn -w 4 -b 0.0.0.0:5000 vidaplus:app
```

## Licença
Projeto licenciado sob MIT.