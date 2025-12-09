# 🎯 Guia Rápido - Migração de SQLite para PostgreSQL

## O que foi feito?

Seu projeto foi modificado para usar **PostgreSQL** em vez de SQLite. Aqui está um resumo das mudanças:

---

## 📝 Arquivos Alterados

### 1. **`pyproject.toml`** - Dependências Atualizadas
```toml
# NOVO: Driver PostgreSQL
"psycopg2-binary>=2.9.9"

# NOVO: Para carregar variáveis de ambiente
"python-dotenv>=1.0.0"
```

**Por quê?**
- `psycopg2-binary`: Permite que Python fale com PostgreSQL
- `python-dotenv`: Carrega credenciais do arquivo `.env` (seguro!)

---

### 2. **`app/database.py`** - Suporte a PostgreSQL

#### ❌ Antes (SQLite fixo):
```python
class DatabaseManager:
    def __init__(self, connection_string="sqlite:///sistema_chamados.db"):
        self.engine = create_engine(connection_string, echo=False)
```

#### ✅ Depois (PostgreSQL configurável):
```python
class DatabaseManager:
    def __init__(self, connection_string=None):
        # Se não passar string, lê do .env
        if connection_string is None:
            db_engine = os.getenv("DB_ENGINE", "postgresql")
            
            if db_engine == "postgresql":
                # Constrói URL: postgresql://usuario:senha@host:porta/banco
                db_user = os.getenv("DB_USER")
                db_password = os.getenv("DB_PASSWORD")
                # ... etc
```

**Por quê?**
- Segurança: Credenciais não ficam no código
- Flexibilidade: Pode usar PostgreSQL ou SQLite
- Profissional: Assim funciona em ambiente real

---

### 3. **`main.py`** - Removido Hardcode

#### ❌ Antes:
```python
self.db_manager = DatabaseManager("sqlite:///sistema_chamados.db")
```

#### ✅ Depois:
```python
self.db_manager = DatabaseManager()  # Lê do .env automaticamente
```

---

## 🔑 Novos Arquivos

### `.env.example` (Template)
Mostra quais variáveis de ambiente você precisa:
```env
DB_ENGINE=postgresql
DB_USER=postgres
DB_PASSWORD=seu_password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=siscall
```

### `.env` (Seus dados reais)
**⚠️ NUNCA commitar no Git!** (já está no `.gitignore`)

Preencha com seus dados do PostgreSQL:
```env
DB_ENGINE=postgresql
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432
DB_NAME=siscall
```

---

## 🚀 Próximos Passos

### 1️⃣ Instalar Dependências Novas
```powershell
# Dentro do projeto, com ambiente virtual ativo
uv sync
```

### 2️⃣ Instalar PostgreSQL
- Download: https://www.postgresql.org/download/
- Ou use Docker: `docker run -e POSTGRES_PASSWORD=postgres -p 5432:5432 -d postgres:15`

### 3️⃣ Criar Banco de Dados
```powershell
psql -U postgres -c "CREATE DATABASE siscall;"
```

### 4️⃣ Preencher `.env` com suas credenciais

### 5️⃣ Rodar a Aplicação
```powershell
python main.py
```

---

## 🎓 Conceitos Importantes para Aprender

### 1. **Connection String (URL de Conexão)**

Ela tell SQLAlchemy como se conectar ao banco:

```
sqlite:///arquivo.db
↓
postgresql://usuario:senha@host:porta/banco
```

### 2. **Variáveis de Ambiente**

Permitem diferentes configurações por máquina:

```
Seu PC (desenvolvimento):    DB_PASSWORD=123
Servidor (produção):         DB_PASSWORD=xyz456secure
```

Sem mudar o código!

### 3. **SQLAlchemy (ORM)**

Intermediário que traduz Python para SQL:

```python
# Python (vosso código)
usuario = session.query(Usuario).filter_by(login="admin").first()

# SQL (o que SQLAlchemy manda para o banco)
SELECT * FROM usuarios WHERE login = 'admin';
```

### 4. **Drivers de Banco de Dados**

```
Seu Código Python
        ↓
    SQLAlchemy (ORM)
        ↓
    psycopg2 (DRIVER) ← Traduz para linguagem PostgreSQL
        ↓
    PostgreSQL (Banco de Dados)
```

Para SQLite, SQLAlchemy usa driver nativo. Para PostgreSQL, precisa de psycopg2.

### 5. **Por que PostgreSQL é melhor que SQLite?**

| Recurso | SQLite | PostgreSQL |
|---------|--------|-----------|
| Arquivo | ✅ (único) | ❌ (servidor) |
| Usuários | ❌ (1) | ✅ (múltiplos) |
| Performance | ❌ (lento com muitos dados) | ✅ (otimizado) |
| Segurança | ❌ (arquivo) | ✅ (autenticação) |
| Deploy | ❌ (copia arquivo) | ✅ (string de conexão) |

---

## 📖 Fluxo de Inicialização (Agora com PostgreSQL)

```
main.py inicia
    ↓
DatabaseManager() é criado
    ↓
Lê arquivo .env
    ↓
Conecta ao PostgreSQL usando credenciais
    ↓
Cria tabelas (se não existirem)
    ↓
Cria usuários padrão
    ↓
Sua aplicação roda! 🎉
```

---

## ❓ Dúvidas Comuns

**P: Por que não usar SQLite em produção?**
R: SQLite é arquivo único. Se 10 usuários tentam acessar ao mesmo tempo, fica lento. PostgreSQL é servidor e aguenta milhares de conexões simultâneas.

**P: Preciso ter PostgreSQL instalado localmente?**
R: Sim, para desenvolvimento. Ou use Docker. Em produção, conecta a um servidor PostgreSQL remoto.

**P: E se eu quiser voltar para SQLite?**
R: Mude o `.env`:
```env
DB_ENGINE=sqlite
DB_PATH=sistema_chamados.db
```
E o código se adapta automaticamente!

**P: O arquivo `.env` com senha é seguro?**
R: Sim, desde que:
- ✅ Nunca commitar no Git
- ✅ Adicionar ao `.gitignore`
- ✅ Cada dev tem seu próprio
- ✅ Em produção, usar variáveis de ambiente do servidor

---

## 🎯 Resumo Final

✅ Seu projeto agora é profissional e escalável
✅ Usa PostgreSQL para dados em produção
✅ Credenciais seguras em arquivo `.env`
✅ Pode mudar de banco sem alterar código
✅ Preparado para crescer!

**Qualquer dúvida, me chama! 😊**
