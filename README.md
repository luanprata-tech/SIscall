GLPI Lite - Sistema de Chamados de Suporte

1.Visão GeralO GLPI Lite é um sistema de gestão de chamados de suporte (Helpdesk) desenvolvido em Python utilizando a biblioteca gráfica PySide6 (Qt). O sistema adota uma arquitetura robusta baseada em MVC (Model-View-Controller) e Padrão de Repositório, garantindo desacoplamento entre a interface, a regra de negócio e o banco de dados.

O objetivo é permitir que usuários abram solicitações de suporte e que administradores/técnicos gerenciem, atendam e finalizem esses chamados, com geração de relatórios gerenciais.

2. Arquitetura Tecnológica
Stack Tecnológico
Linguagem: Python 3.10+
Interface Gráfica (GUI): PySide6 (Qt for Python)
Banco de Dados: SQLite (Padrão) / Agnóstico (via SQLAlchemy)
ORM: SQLAlchemy (Mapeamento Objeto-Relacional)

Estrutura de PastasO projeto segue uma estrutura modular:/projeto
│
├── main.py                 # Ponto de entrada da aplicação (Inicialização)
├── sistema_chamados.db     # Arquivo do banco de dados (gerado automaticamente)
│
└── app/                    # Pacote principal da aplicação
    ├── __init__.py         # Identificador de pacote Python
    ├── database.py         # Configuração do DB e Modelos (Entities)
    ├── repositories.py     # Camada de Acesso a Dados (CRUD puro)
    ├── controllers.py      # Regras de Negócio e Validações
    └── views.py            # Interface Gráfica (Janelas, Estilos, Widgets)

Decisões de Design
SQLAlchemy ORM: Utilizado para que o sistema não dependa de sintaxe SQL específica. Para mudar de SQLite para PostgreSQL ou MySQL, basta alterar a Connection String em database.py.

Injeção de Dependência: O main.py instancia o banco, passa para o repositório, que é passado para o controller, que é injetado na View. Isso facilita testes e manutenção.

Estilização: Uso de Qt Style Sheets (CSS-like) centralizado em STYLESHEET no arquivo views.py para facilitar a mudança de temas (Modo Escuro/Claro).

3. Instalação e Execução

Pré-requisitosPython 3.10 ou superior instalado.
Gerenciador de pacotes pip ou uv.

Instalação das Dependências
No terminal, execute:

# Usando pip
pip install PySide6 SQLAlchemy
# OU usando uv (recomendado)
uv add PySide6 SQLAlchemy
Nota para Linux: Se houver erro ao abrir a janela, instale a libxcb:sudo apt-get install libxcb-cursor0

Executando o Sistema
python main.py

Na primeira execução, o sistema criará automaticamente o arquivo de banco de dados e o usuário administrador padrão.

4. Funcionalidades e Perfis

A. Acesso Inicial (Credenciais Padrão)
O sistema gera dois usuários automaticamente na primeira execução:
Administrador: Login: admin / Senha: admin123
Usuário Comum: Login: user / Senha: user123

B. Perfil: Usuário Comum
Abrir Chamado:
Seleciona a máquina/dispositivo afetado.
Descreve o problema.
Data e Hora são registradas automaticamente.

Meus Chamados:
Visualiza histórico próprio em tabela.
Exclusão: Pode excluir chamados apenas se o status for "Aberto".

Troca de Senha:
Se o admin resetou a senha, o usuário é forçado a criar uma nova no primeiro login.


C. Perfil: Administrador (Suporte)
Dashboard de Tarefas (Pendentes):
Visualização em tempo real de chamados "Aberto" ou "Em andamento".
Destaque visual (pisca em vermelho/branco) para chamados criados nos últimos 16 segundos.

Histórico Completo:
Visualiza todos os chamados, inclusive finalizados.

Fluxo de Atendimento:
Iniciar: 
O admin assume um chamado.
O status muda para "Em andamento" e o horário de início é gravado.

Bloqueio: 
Outros admins veem o chamado como "Bloqueado" e quem está atendendo.

Finalizar: 
O admin deve preencher "Diagnóstico" e "Solução".
O status muda para "Finalizado" e o horário de fim é gravado.

Relatórios Gerenciais:

Filtro por período (Data Início/Fim).
Métricas: Setor com mais chamados, Máquina mais problemática, Suporte mais produtivo e Tempo Médio de Resolução.

Configurações (Gestão de Usuários):
CRUD de usuários.
Alterar setor e cargo (Promover a Admin / Rebaixar a User).
Reset de Senha: Define uma senha provisória que obriga o usuário a trocar no próximo acesso.

5. Modelo de Dados (Schema)
Tabela:usuarios
Coluna  Tipo        Descrição   
id      Integer(PK) Identificador único
nome    String      Nome completo
login   String      Login único para acesso
senha   String      Hash da senha (SHA256)
tipo    Integer     0 = Usuário, 1 = Admin
setor   String      Departamento (RH, TI, etc.)
trocar_senha    Boolean     Flag para forçar troca de senha

Tabela: chamados
Coluna      Tipo            Descrição
id          Integer(PK)     Identificador do chamado
usuario_id  Integer(FK)     Quem abriu o chamado
suporte_id  Integer(FK)     Quem atendeu (Admin)
maquina     String          Dispositivo afetado 
descricao   String          Relato do problema  
status      String          Aberto, Em andamento, Finalizado
data_abertura   DateTime    Data de criação
data_inicio     DateTime    Quando o suporte assumiu
data_fechamento DateTime    Quando foi finalizado
diagnostico String          Análise técnica
solucao     String          Ação corretiva realizada

6. Manutenção e Evolução
Mudando o Banco de Dados
Para usar PostgreSQL ou MySQL em produção:
Instale o driver (ex: pip install psycopg2).
No arquivo app/database.py, altere a linha:

# De:
self.engine = create_engine("sqlite:///sistema_chamados.db")

# Para:
self.engine = create_engine("postgresql://user:pass@localhost/meubanco")

O SQLAlchemy criará as tabelas automaticamente.

Customização de Tema
As cores e fontes são definidas na constante STYLESHEET em app/views.py.
Verde Principal: #4CAF50
Vermelho (Alerta/Aberto): #d32f2f
Menu Lateral: #2c3e507. 

Troubleshooting (Solução de Problemas)
Erro "no such column": Ocorre se você alterou o código (models) mas manteve o banco antigo (.db).
Solução: Delete o arquivo sistema_chamados.db e reinicie o programa.
Botões cortados: Pode ocorrer em resoluções de tela muito baixas ou escalas de DPI altas no Windows.
Solução: O sistema tenta forçar showMaximized(), mas ajustes nas larguras das colunas em app/views.py podem ser necessários dependendo do monitor.