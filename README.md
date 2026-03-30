# SisCall - Sistema de Chamados de Suporte

## 📋 Visão Geral
O **SisCall** é um sistema de gestão de chamados de suporte (Helpdesk) desenvolvido em Python utilizando a biblioteca gráfica **PySide6 (Qt)**. O sistema foi projetado para ser robusto e escalável, suportando **PostgreSQL**, **MySQL** e **SQLite** via **SQLAlchemy**.

O sistema permite que usuários abram solicitações de suporte técnico e de criação de contas em sistemas, enquanto administradores gerenciam, atendem e finalizam esses chamados, com acesso a relatórios gerenciais e um dashboard em tempo real.

## 🚀 Funcionalidades Principais

### 👤 Painel do Usuário
- **Abertura de Chamados:** Registro de incidentes por tipo de dispositivo.
- **Solicitação de Contas:** Fluxo específico para solicitar acesso a sistemas (IGESP, EXPRESSO, etc.).
- **Meus Chamados:** Acompanhamento do status e histórico.
- **Cadastro de Usuários:** Perfil de "Responsável" (Tipo 2) pode cadastrar novos usuários.

### 🛠️ Painel Administrativo (Suporte)
- **Gestão de Chamados:** Visualização de pendentes, atendimento e finalização.
- **Solicitações de Conta:** Aprovação e processamento de acessos.
- **Relatórios:** Métricas de desempenho, setores com mais chamados, etc.
- **Gestão de Usuários:** CRUD completo de usuários e permissões.

### 📺 Dashboard (TV Mode)
- Aplicação dedicada (`dashboard.py`) para monitoramento em tempo real em telas grandes.
- Alertas sonoros e visuais para novos chamados.

## 🛠️ Tecnologias Utilizadas
- **Linguagem:** Python 3.10+
- **Interface:** PySide6 (Qt for Python)
- **Banco de Dados:** PostgreSQL, MySQL ou SQLite
- **ORM:** SQLAlchemy
- **Gerenciamento de Dependências:** UV (ou Pip)

## 📚 Documentação
A documentação completa do projeto está na pasta `docs/`. Recomendamos a leitura na seguinte ordem:

1. **QUICKSTART.md** - Guia rápido para rodar em 5 minutos.
2. **SETUP_POSTGRESQL.md** - Guia detalhado de instalação do banco de dados.
3. **MIGRAÇÃO_EXPLICADA.md** - Entenda a arquitetura e a migração para PostgreSQL.

## ⚡ Como Rodar (Resumo)

1. **Instale as dependências:**
   ```powershell
   uv sync
   ```

2. **Configure o Banco de Dados:**
   - Crie um banco (PostgreSQL ou MySQL) chamado `siscall`.
   - Copie o arquivo `.env.example` para `.env` e configure suas credenciais.

3. **Execute a Aplicação:**
   ```powershell
   python main.py
   ```

4. **Execute o Dashboard (Opcional):**
   ```powershell
   python dashboard.py
   ```

## 🔐 Acesso Inicial
Se for a primeira execução (banco vazio), o sistema criará um usuário administrador padrão:
- **Login:** `admin`
- **Senha:** `admin123`

## Comando do executavel
uv run  PyInstaller --noconfirm --clean --name SisCall --onedir --windowed --icon "assets\icon.ico" --add-data ".env;.config" --add-data "assets;assets" --distpath
"dist" --workpath "build" "main.py"