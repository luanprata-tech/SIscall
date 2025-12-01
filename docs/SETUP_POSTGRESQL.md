# SisCall - Sistema de Chamados

## 🚀 Setup do Projeto

### 1. Clonar e Entrar no Projeto
```powershell
git clone https://github.com/luanprata-tech/SIscall.git
cd SIscall
```

### 2. Instalar Dependências com UV

#### 📥 Se não tem UV instalado:
```powershell
pip install uv
```

#### 🔄 Sincronizar ambiente virtual e dependências:
```powershell
uv sync
```

Isso vai:
- ✅ Criar automaticamente o `.venv/` (ambiente virtual)
- ✅ Instalar todas as dependências do `pyproject.toml`
- ✅ Criar arquivo `uv.lock` com versões exatas

#### ✅ Ativar o ambiente virtual:

**No PowerShell:**
```powershell
.\.venv\Scripts\Activate.ps1
```

Se receber erro de permissão:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 3. Configurar Banco de Dados

#### 📝 Criar arquivo `.env`

Na raiz do projeto, copie o arquivo exemplo:
```powershell
Copy-Item .env.example .env
```

Agora edite o arquivo `.env` com suas credenciais do PostgreSQL:

```env
# Configuração para PostgreSQL
DB_ENGINE=postgresql
DB_USER=seu_usuario_postgres
DB_PASSWORD=sua_senha
DB_HOST=localhost
DB_PORT=5432
DB_NAME=siscall
```

#### 🐘 Instalar PostgreSQL

**Windows:**
1. Baixe em: https://www.postgresql.org/download/windows/
2. Execute o instalador
3. Anote o usuário e senha que definir na instalação
4. Confirme que a porta é 5432

**Alternativa: Usar Docker**
```powershell
docker run --name siscall-postgres -e POSTGRES_PASSWORD=postgres -p 5432:5432 -d postgres:15
```

#### ✅ Criar banco de dados PostgreSQL

```powershell
# Conectar ao PostgreSQL
psql -U postgres

# Dentro do psql, criar o banco:
CREATE DATABASE siscall;

# Sair
\q
```

Ou via pgAdmin (ferramenta gráfica).

### 4. Executar a Aplicação

```powershell
python main.py
```

---

## 📚 Entendendo a Migração SQLite → PostgreSQL

### Por que PostgreSQL?

| Aspecto | SQLite | PostgreSQL |
|--------|--------|-----------|
| **Escala** | Arquivo local | Servidor profissional |
| **Usuários** | Limite local | Múltiplos usuários simultâneos |
| **Performance** | Lento com muitos dados | Otimizado para grandes volumes |
| **Segurança** | Arquivo no disco | Autenticação, permissões |
| **Deploy** | Copia arquivo | String de conexão segura |

### 🔑 Conceitos Principais

#### 1️⃣ **Connection String (URL de Conexão)**

SQLite:
```python
"sqlite:///sistema_chamados.db"  # Arquivo local
```

PostgreSQL:
```python
"postgresql://usuario:senha@host:porta/banco"
# Exemplo:
"postgresql://postgres:senha123@localhost:5432/siscall"
```

#### 2️⃣ **Variáveis de Ambiente (`.env`)**

Em vez de hardcoding credenciais no código:

```python
# ❌ INSEGURO - Credenciais no código
connection_string = "postgresql://postgres:senha123@localhost:5432/siscall"

# ✅ SEGURO - Lê do arquivo .env
os.getenv("DB_PASSWORD")  # Lê da variável de ambiente
```

**Vantagens:**
- Credenciais não ficam no Git
- Cada máquina/dev tem suas próprias credenciais
- Fácil mudar entre desenvolvimento e produção

#### 3️⃣ **Driver de Banco de Dados (psycopg2)**

SQLAlchemy é o "intermediário" entre Python e PostgreSQL:

```
Python Code → SQLAlchemy → psycopg2 (driver) → PostgreSQL
```

O `psycopg2-binary` é o driver que fala com PostgreSQL.

#### 4️⃣ **scoped_session**

Importante para aplicações com threads (como GUI):

```python
# Cada thread tem sua própria sessão
Session = scoped_session(sessionmaker(bind=engine))

# Evita conflitos de acesso simultâneo
```

---

## 🔧 Configuração Avançada

### Usar SQLite (Desenvolvimento Local)

Edite `.env`:
```env
DB_ENGINE=sqlite
DB_PATH=./data/sistema_chamados.db
```

### Conectar em PostgreSQL Remoto

Edite `.env`:
```env
DB_ENGINE=postgresql
DB_USER=usuario_remoto
DB_PASSWORD=senha_remota
DB_HOST=seu-servidor.com.br
DB_PORT=5432
DB_NAME=siscall_producao
```

### Debug: Ver SQL Queries

No `database.py`, mude para `echo=True`:
```python
self.engine = create_engine(connection_string, echo=True)
```

---

## 📦 Dependências Instaladas

| Pacote | Versão | Motivo |
|--------|--------|--------|
| `pyside6` | >=6.10.1 | Interface Gráfica |
| `sqlalchemy` | >=2.0.44 | ORM de Banco de Dados |
| `psycopg2-binary` | >=2.9.9 | Driver PostgreSQL |
| `python-dotenv` | >=1.0.0 | Carregar variáveis `.env` |

---

## ⚠️ Troubleshooting

### Erro: `could not connect to server`

**Causa:** PostgreSQL não está rodando ou credenciais erradas.

**Solução:**
```powershell
# Verificar se PostgreSQL está ativo (Windows)
Get-Service postgresql-x64-15

# Se não estiver, inicie:
Start-Service postgresql-x64-15
```

### Erro: `FATAL: database "siscall" does not exist`

**Solução:** Criar o banco:
```powershell
psql -U postgres -c "CREATE DATABASE siscall;"
```

### Erro: `psycopg2 not found`

**Solução:** Reinstalar dependências:
```powershell
uv sync --force
```

---

## 🎓 Aprendizados

✅ **Migração de SQLite para PostgreSQL**
✅ **Uso de variáveis de ambiente para segurança**
✅ **Configuração dinâmica de banco de dados**
✅ **SQLAlchemy com drivers diferentes**
✅ **Boas práticas de desenvolvimento**

---

**Desenvolvido com ❤️ por Luan Prata**
