# 🚀 QUICK START - PostgreSQL + Python

## 1️⃣ Instalar Dependências Novas

```powershell
# Ativar ambiente virtual
.\.venv\Scripts\Activate.ps1

# Sincronizar com uv (instala psycopg2 e python-dotenv)
uv sync
```

---

## 2️⃣ Instalar PostgreSQL

**Windows:**
- Baixe: https://www.postgresql.org/download/windows/
- Instale com porta 5432
- Anote a senha do usuário `postgres`

**Ou use Docker (mais fácil):**
```powershell
docker run --name siscall-postgres -e POSTGRES_PASSWORD=postgres -p 5432:5432 -d postgres:15
```

---

## 3️⃣ Criar Banco de Dados

```powershell
psql -U postgres
```

Dentro do psql:
```sql
CREATE DATABASE siscall;
\q
```

---

## 4️⃣ Configurar `.env`

O arquivo já foi criado em:
`c:\Users\Luan Prata\Desktop\SisCall\SIscall\.env`

Verifique se está assim:
```env
DB_ENGINE=postgresql
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432
DB_NAME=siscall
```

**Mude `DB_PASSWORD` se você definiu outra senha no PostgreSQL**

---

## 5️⃣ Rodar a Aplicação

```powershell
python main.py
```

A aplicação vai:
1. Ler o `.env`
2. Conectar ao PostgreSQL
3. Criar tabelas automaticamente
4. Abrir a interface gráfica

---

## ✨ Resultado

| Antes (SQLite) | Depois (PostgreSQL) |
|---|---|
| Arquivo local | Servidor |
| 1 usuário | Múltiplos usuários |
| Lento com muitos dados | Rápido e escalável |
| `sistema_chamados.db` | `postgresql://...` |

---

## 📚 Arquivos Criados para Aprender

| Arquivo | Conteúdo |
|---------|----------|
| `RESUMO_ALTERACOES.md` | Quais arquivos foram mudados |
| `SETUP_POSTGRESQL.md` | Guia completo de instalação |
| `MIGRAÇÃO_EXPLICADA.md` | Conceitos educativos |
| `schema_postgres.sql` | Script SQL para criar tabelas |
| `.env.example` | Template das variáveis necessárias |

---

## 🎯 Checklist

- [ ] Dependências instaladas com `uv sync`
- [ ] PostgreSQL instalado
- [ ] Banco `siscall` criado
- [ ] `.env` preenchido com suas credenciais
- [ ] `python main.py` funciona sem erros

---

## ❌ Se der erro

1. **"could not connect to server"**
   - PostgreSQL não está rodando
   - Verifique a senha no `.env`

2. **"database siscall does not exist"**
   - Execute: `psql -U postgres -c "CREATE DATABASE siscall;"`

3. **"psycopg2 not found"**
   - Execute: `uv sync --force`

4. **Porta já em uso**
   - Outra aplicação usando porta 5432
   - Mude a porta no `.env` e no PostgreSQL

---

**Pronto? Bora rodar! 🎉**
