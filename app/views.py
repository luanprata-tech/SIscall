from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, 
    QHeaderView, QMessageBox, QComboBox, QPlainTextEdit,
    QAbstractItemView, QDialog, QStackedWidget, QFrame, QScrollArea,
    QInputDialog, QDateEdit, QGroupBox, QGridLayout, QCheckBox
)
from PySide6.QtCore import Qt, QTimer, QTime, QDate
from PySide6.QtGui import QIcon, QGuiApplication, QColor, QFont
import traceback 
from datetime import datetime, timedelta 

# --- ESTILOS GLOBAIS ---
STYLESHEET = """
QMainWindow, QDialog { background-color: #f0f3f4; }
QWidget { font-family: 'Segoe UI', sans-serif; font-size: 14px; }
QLabel { color: #333333; }

/* Botões Padrão */
QPushButton { 
    background-color: #458BD2; color: white; border-radius: 4px; 
    padding: 8px 16px; font-weight: bold; border: none;
}
QPushButton:hover { background-color: #537DA7; }
QPushButton:disabled { background-color: #bdc3c7; color: #7f8c8d; }
QPushButton#Danger { background-color: #d32f2f; }
QPushButton#Info { background-color: #2196F3; } 
QPushButton#Secondary { background-color: #757575; }
QPushButton#Link { background-color: transparent; color: #537DA7; border: none; text-decoration: underline;}

/* Botão de Submit (Verde Grande) */
QPushButton#SubmitBtn { 
    background-color: #458BD2; color: white; border: none;
    border-radius: 4px; font-size: 16px; padding: 12px; font-weight: bold;
}
QPushButton#SubmitBtn:hover { background-color: #537DA7; }

/* Menu Lateral */
QWidget#Sidebar { background-color: #2c3e50; min-width: 220px; max-width: 220px; }
QPushButton#MenuBtn { background-color: transparent; color: #ecf0f1; text-align: left; padding: 12px 20px; border: none; font-size: 15px; }
QPushButton#MenuBtn:hover { background-color: #34495e; border-left: 4px solid #4CAF50; }
QPushButton#MenuBtn:checked { background-color: #34495e; border-left: 4px solid #4CAF50; font-weight: bold; }
QLabel#MenuTitle { color: white; font-size: 20px; font-weight: bold; padding: 30px 10px; }

/* Tabelas */
QTableWidget { 
    background-color: white; color: #333333; selection-background-color: #e3f2fd; selection-color: black; border: 1px solid #ddd;
    font-size: 14px; alternate-background-color: #fafafa;
}
QTableWidget::item { padding: 10px; border-bottom: 1px solid #f0f0f0; }
QHeaderView::section { background-color: #34495e; color: white; padding: 10px; border: none; font-weight: bold; font-size: 14px; }

/* Inputs */
QLineEdit, QPlainTextEdit, QComboBox, QDateEdit { 
    border: 1px solid #ccc; border-radius: 4px; padding: 8px; 
    background-color: white; color: #333333; 
}
QComboBox QAbstractItemView {
    background-color: white; color: #333333; selection-background-color: #4CAF50; selection-color: white;
    border: 1px solid #ccc; outline: none;
}

/* Cards de Relatório */
QGroupBox {
    background-color: white; border: 1px solid #ddd; border-radius: 8px; margin-top: 20px; font-weight: bold; color: #2c3e50;
}
QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }
QLabel#MetricValue { font-size: 24px; font-weight: bold; color: #2E7D32; }
QLabel#MetricLabel { font-size: 14px; color: #7f8c8d; }
"""

class CenterMixin:
    def force_center(self):
        screen = QGuiApplication.primaryScreen().availableGeometry()
        size = self.geometry()
        x = (screen.width() - size.width()) // 2
        y = (screen.height() - size.height()) // 2
        self.move(x, y)
    def showEvent(self, event):
        super().showEvent(event)
        if not getattr(self, '_centered', False):
            QTimer.singleShot(10, self.force_center)
            self._centered = True

# --- JANELA DE TROCA DE SENHA OBRIGATÓRIA ---
class ChangePasswordDialog(QDialog, CenterMixin):
    def __init__(self, auth_controller, user_id, on_success, parent=None):
        super().__init__(parent)
        self.auth = auth_controller
        self.user_id = user_id
        self.on_success = on_success
        self.setWindowTitle("Definir Nova Senha")
        self.setFixedSize(400, 300)
        self.setWindowFlags(Qt.Window | Qt.WindowTitleHint | Qt.CustomizeWindowHint) 
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        lbl = QLabel("⚠️ Sua senha é provisória.\nPor favor, defina uma nova senha.")
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: #d32f2f; margin-bottom: 20px;")
        self.txt_pass = QLineEdit(); self.txt_pass.setPlaceholderText("Nova Senha"); self.txt_pass.setEchoMode(QLineEdit.Password)
        self.txt_confirm = QLineEdit(); self.txt_confirm.setPlaceholderText("Confirmar"); self.txt_confirm.setEchoMode(QLineEdit.Password)
        btn = QPushButton("Salvar e Entrar"); btn.setObjectName("SubmitBtn"); btn.clicked.connect(self.salvar)
        layout.addWidget(lbl); layout.addWidget(self.txt_pass); layout.addWidget(self.txt_confirm); layout.addWidget(btn)

    def salvar(self):
        if self.txt_pass.text() != self.txt_confirm.text():
            QMessageBox.warning(self, "Erro", "As senhas não coincidem.")
            return
        try:
            self.auth.alterar_senha_definitiva(self.user_id, self.txt_pass.text())
            QMessageBox.information(self, "Sucesso", "Senha alterada!")
            self.accept()
            self.on_success() 
        except Exception as e: QMessageBox.warning(self, "Erro", str(e))

# --- DIALOGO DE EDIÇÃO DE USUÁRIO (ADMIN) ---
class UserEditDialog(QDialog, CenterMixin):
    def __init__(self, auth_controller, user_data, parent=None):
        super().__init__(parent)
        self.auth = auth_controller
        self.user = user_data
        self.setWindowTitle(f"Gerenciar: {user_data.nome}")
        self.setFixedSize(450, 500)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        layout.addWidget(QLabel(f"<b>Nome:</b> {self.user.nome}"))
        layout.addWidget(QLabel(f"<b>Login:</b> {self.user.login}"))
        
        # CARGO (NOVO: Permitir dar/tirar admin)
        layout.addWidget(QLabel("<b>Cargo / Permissão:</b>"))
        self.combo_tipo = QComboBox()
        self.combo_tipo.addItems(["Usuário", "Administrador"])
        # 0=User, 1=Admin. Se for 1, seleciona index 1.
        self.combo_tipo.setCurrentIndex(1 if self.user.tipo == 1 else 0)
        layout.addWidget(self.combo_tipo)

        # SETOR
        layout.addWidget(QLabel("<b>Setor:</b>"))
        self.combo_setor = QComboBox()
        self.combo_setor.addItems(["GERH", "ASCOM", "COTRANSP", "GEATEC", "GEINFORM", "GECONF", "GEAAD", "PROJUR", "DIRAF","DITEC","AGEPLAN","PRESIDENCIA","OUVIDORIA","PROTOCOLO","AUDITORIO","LABAGUA","CONSEGER","GEMETRO","GEREMETRO","COMEL","AGEQUALI","CPI","ARRECADAÇÂO","FISCAIS","LABAGUA","LEI","LABORG","LABROMO","LABSOLOS","LABMICRO","PRE-MEDIDOS","GUARITA"])
        self.combo_setor.setCurrentText(self.user.setor)
        layout.addWidget(self.combo_setor)
        
        btn_save = QPushButton("Salvar Alterações")
        btn_save.clicked.connect(self.salvar_alteracoes)
        layout.addWidget(btn_save)
        
        layout.addWidget(QLabel("<hr>"))
        layout.addWidget(QLabel("<b>Redefinir Senha (Provisória):</b>"))
        self.txt_senha = QLineEdit(); self.txt_senha.setPlaceholderText("Nova senha temporária")
        layout.addWidget(self.txt_senha)
        btn_senha = QPushButton("Definir Senha"); btn_senha.setObjectName("Info"); btn_senha.clicked.connect(self.resetar_senha)
        layout.addWidget(btn_senha)
        layout.addStretch()

    def salvar_alteracoes(self):
        try:
            # Atualiza Setor
            self.auth.atualizar_setor(self.user.id, self.combo_setor.currentText())
            # Atualiza Cargo
            novo_tipo = 1 if self.combo_tipo.currentIndex() == 1 else 0
            if novo_tipo != self.user.tipo:
                self.auth.alterar_cargo_usuario(self.user.id, novo_tipo)
            QMessageBox.information(self, "Sucesso", "Dados atualizados!")
        except Exception as e: QMessageBox.warning(self, "Erro", str(e))

    def resetar_senha(self):
        try:
            self.auth.definir_senha_provisoria(self.user.id, self.txt_senha.text())
            QMessageBox.information(self, "Sucesso", "Senha redefinida!")
            self.txt_senha.clear()
        except Exception as e: QMessageBox.warning(self, "Erro", str(e))

# --- JANELA DE AÇÃO DO SUPORTE ---
class TicketActionDialog(QDialog, CenterMixin):
    def __init__(self, chamado_id, controller, user_suporte, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.chamado_id = chamado_id
        self.user_suporte = user_suporte
        self.setWindowTitle(f"Atendimento Chamado #{chamado_id}")
        # Correção para fundo da janela
        self.setStyleSheet("background-color: #fdfdfd; color: #333333;")
        self.setup_ui()
        self.load_chamado()

    def setup_ui(self):
        c = self.controller.buscar_por_id(self.chamado_id)
        if c.status == "Aberto": self.setFixedSize(600,500) #Para definir o tamanho da janela de detalhes de acordo com cara status
        else: self.setFixedSize(600,700)
        self.layout = QVBoxLayout(self)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background-color: #fdfdfd; border: none;") 
        scroll_content = QWidget()
        scroll_content.setStyleSheet("background-color: #fdfdfd;")
        self.details_layout = QVBoxLayout(scroll_content)
        self.lbl_info = QLabel()
        self.lbl_info.setStyleSheet("font-size: 15px; line-height: 1.5; color: #333;")
        self.lbl_info.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.details_layout.addWidget(self.lbl_info)
        self.details_layout.addSpacing(10)
        scroll.setWidget(scroll_content)
        self.layout.addWidget(scroll)
        self.action_frame = QFrame()
        self.action_frame.setStyleSheet("QFrame { background-color: #C4CFED; border-radius: 5px; padding: 10px; border: 1px solid #9DA2AE; } QLabel { color: #333; }")
        self.action_layout = QVBoxLayout(self.action_frame)
        self.layout.addWidget(self.action_frame)

    def load_chamado(self):
        c = self.controller.buscar_por_id(self.chamado_id)
        if not c: self.close(); return
        info_text = f"""
        <h3 style='margin:0; color:#2c3e50;'>{c.nome_usuario}</h3>
        <span style='color:#7f8c8d;'>{c.setor_usuario}</span><br><br>
        <b>Máquina:</b> {c.maquina}<br>
        <b>Aberto em:</b> {c.data_abertura}<br>
        <b>Status:</b> <b style='font-size:16px; color:{'red' if c.status=='Aberto' else 'blue'}'>{c.status.upper()}</b><br>
        <hr>
        <b>Descrição:</b><br>
        <div style='background-color:#fff; padding:10px; border-radius:4px; border:1px solid #ddd; color: #333;'>{c.descricao}</div>
        """
        
        # Se for solicitação de criação de conta, mostrar sistemas solicitados
        if c.maquina == "Solicitação de Criação de Conta" and c.contas_solicitadas:
            info_text += f"""
        <br><hr>
        <b>Sistemas para Criação de Conta:</b><br>
        <div style='background-color:#e8f4f8; padding:10px; border-radius:4px; border:1px solid #add8e6; color: #333;'>
        {c.contas_solicitadas.replace(',', '<br>')}
        </div>
        """
        
        self.lbl_info.setText(info_text)
        while self.action_layout.count():
            child = self.action_layout.takeAt(0)
            if child.widget(): child.widget().deleteLater()
        if c.status == "Aberto": self.build_start_ui()
        elif c.status == "Em andamento":
            if c.suporte_id == self.user_suporte.id: self.build_finish_ui(c)
            else: self.build_locked_ui(c)
        else: self.build_readonly_ui(c)

    def build_start_ui(self):
        lbl = QLabel("Este chamado está aguardando atendimento.")
        btn_start = QPushButton("Iniciar Atendimento")
        btn_start.setObjectName("SubmitBtn")
        btn_start.clicked.connect(self.iniciar_atendimento)
        self.action_layout.addWidget(lbl)
        self.action_layout.addWidget(btn_start)

    def build_finish_ui(self, chamado):
        lbl = QLabel(f"<b>Em atendimento desde:</b> {chamado.data_inicio_atendimento}")
        btn_finish = QPushButton("Finalizar Chamado")
        btn_finish.setObjectName("SubmitBtn")
        btn_finish.clicked.connect(self.finalizar_atendimento)
        
        self.action_layout.addWidget(lbl)
        
        # Verificar se é uma solicitação de criação de conta
        if chamado.maquina == "Solicitação de Criação de Conta":
            # Para criação de conta: mostrar apenas um campo com login e senha
            self.action_layout.addWidget(QLabel("Credenciais Criadas:"))
            self.txt_solucao = QPlainTextEdit()
            self.txt_solucao.setPlaceholderText("Digite o login e senha separados por | (exemplo: usuario.nome | senha123)")
            self.txt_solucao.setStyleSheet("background-color: white; color: #333;")
            self.action_layout.addWidget(self.txt_solucao)
        else:
            # Para chamados normais: diagnóstico e solução
            self.txt_diag = QPlainTextEdit()
            self.txt_diag.setPlaceholderText("Diagnóstico técnico...")
            self.txt_diag.setStyleSheet("background-color: white; color: #333;")
            self.txt_solucao = QPlainTextEdit()
            self.txt_solucao.setPlaceholderText("Solução aplicada...")
            self.txt_solucao.setStyleSheet("background-color: white; color: #333;")
            self.action_layout.addWidget(QLabel("Diagnóstico:"))
            self.action_layout.addWidget(self.txt_diag)
            self.action_layout.addWidget(QLabel("Solução:"))
            self.action_layout.addWidget(self.txt_solucao)
        
        self.action_layout.addWidget(btn_finish)


    def build_readonly_ui(self, chamado):
        # Verificar se é uma solicitação de conta
        if chamado.maquina == "Solicitação de Criação de Conta":
            info = f"<b>Responsável:</b> {chamado.nome_suporte}<br><b>Início:</b> {chamado.data_inicio_atendimento} | <b>Fim:</b> {chamado.data_fechamento}<br><br><b>Credenciais Criadas:</b><br><div style='background-color:#e8f4f8; padding:10px; border-radius:4px; border:1px solid #add8e6; color: #333;'>{chamado.solucao}</div>"
        else:
            info = f"<b>Responsável:</b> {chamado.nome_suporte}<br><b>Início:</b> {chamado.data_inicio_atendimento} | <b>Fim:</b> {chamado.data_fechamento}<br><br><b>Diagnóstico:</b> {chamado.diagnostico}<br><b>Solução:</b> {chamado.solucao}"
        lbl = QLabel(info)
        lbl.setWordWrap(True)
        self.action_layout.addWidget(lbl)

    def iniciar_atendimento(self):
        try: self.controller.assumir_chamado(self.chamado_id, self.user_suporte.id); QMessageBox.information(self, "Sucesso", "Chamado em execução!"); self.load_chamado()
        except Exception as e: QMessageBox.warning(self, "Erro", str(e))

    def finalizar_atendimento(self):
        try:
            c = self.controller.buscar_por_id(self.chamado_id)
            if c.maquina == "Solicitação de Criação de Conta":
                # Para contas, não precisa de diagnóstico
                self.controller.finalizar_chamado(self.chamado_id, self.user_suporte.id, "", self.txt_solucao.toPlainText())
            else:
                # Para chamados normais
                self.controller.finalizar_chamado(self.chamado_id, self.user_suporte.id, self.txt_diag.toPlainText(), self.txt_solucao.toPlainText())
            QMessageBox.information(self, "Sucesso", "Chamado finalizado!")
            self.accept()
        except Exception as e:
            QMessageBox.warning(self, "Erro", str(e))

# --- CADASTRO ---
class RegisterWindow(QDialog, CenterMixin):
    def __init__(self, auth_controller, parent=None):
        super().__init__(parent)
        self.auth = auth_controller
        self.setWindowTitle("Novo Usuário")
        self.setFixedSize(350, 450)
        self.setup_ui()
    def setup_ui(self):
        layout = QVBoxLayout(self); layout.setAlignment(Qt.AlignTop)
        self.txt_nome = QLineEdit(); self.txt_nome.setPlaceholderText("Nome")
        self.txt_sobrenome = QLineEdit(); self.txt_sobrenome.setPlaceholderText("Sobrenome")
        self.txt_login = QLineEdit(); self.txt_login.setPlaceholderText("Login")
        self.txt_senha = QLineEdit(); self.txt_senha.setPlaceholderText("Senha"); self.txt_senha.setEchoMode(QLineEdit.Password)
        self.combo_setor = QComboBox(); self.combo_setor.addItems(["Selecione seu Setor","GERH", "ASCOM", "COTRANSP", "GEATEC", "GEINFORM", "GECONF", "GEAAD", "PROJUR", "DIRAF","DITEC","AGEPLAN","PRESIDENCIA","OUVIDORIA","PROTOCOLO","AUDITORIO","LABAGUA","CONSEGER","GEMETRO","GEREMETRO","COMEL","AGEQUALI","CPI","ARRECADAÇÂO","FISCAIS","LABAGUA","LEI","LABORG","LABROMO","LABSOLOS","LABMICRO","PRE-MEDIDOS","GUARITA" ])
        btn_save = QPushButton("Criar Conta"); btn_save.clicked.connect(self.registrar); btn_save.setAutoDefault(False)
        btn_cancel = QPushButton("Cancelar"); btn_cancel.setObjectName("Secondary"); btn_cancel.clicked.connect(self.close)
        layout.addWidget(QLabel("Crie sua conta")); layout.addWidget(self.txt_nome); layout.addWidget(self.txt_sobrenome); layout.addWidget(self.combo_setor); layout.addWidget(self.txt_login); layout.addWidget(self.txt_senha); layout.addSpacing(10); layout.addWidget(btn_save); layout.addWidget(btn_cancel)
    def registrar(self):
        try: self.auth.cadastrar_usuario(self.txt_nome.text(), self.txt_sobrenome.text(), self.txt_login.text(), self.txt_senha.text(), self.combo_setor.currentText()); QMessageBox.information(self, "Sucesso", "Usuário criado! Faça login."); self.close()
        except Exception as e: QMessageBox.warning(self, "Erro", str(e))

# --- LOGIN ---
class LoginWindow(QMainWindow, CenterMixin):
    def __init__(self, auth_controller, on_success_callback):
        super().__init__()
        self.auth = auth_controller
        self.on_success = on_success_callback
        self.logging_in = False
        self.setWindowTitle("Sistema de Chamados")
        self.setFixedSize(400, 350)
        self.setup_ui()
    def setup_ui(self):
        central = QWidget(); self.setCentralWidget(central); layout = QVBoxLayout(central); layout.setAlignment(Qt.AlignCenter)
        title = QLabel("Login"); title.setObjectName("Title"); title.setStyleSheet("font-size: 24px; color: #537DA7; font-weight: bold;")
        self.txt_user = QLineEdit(); self.txt_user.setPlaceholderText("Usuário"); self.txt_user.returnPressed.connect(self.perform_login)
        self.txt_pass = QLineEdit(); self.txt_pass.setPlaceholderText("Senha"); self.txt_pass.setEchoMode(QLineEdit.Password); self.txt_pass.returnPressed.connect(self.perform_login)
        btn_login = QPushButton("Entrar"); btn_login.clicked.connect(self.perform_login); btn_login.setAutoDefault(False); btn_login.setDefault(False)
        btn_register = QPushButton("Não tem conta? Cadastre-se"); btn_register.setObjectName("Link"); btn_register.setCursor(Qt.PointingHandCursor); btn_register.clicked.connect(self.open_register)
        layout.addWidget(title); layout.addWidget(self.txt_user); layout.addWidget(self.txt_pass); layout.addWidget(btn_login); layout.addWidget(btn_register)
    def perform_login(self):
        if self.logging_in: return
        self.logging_in = True
        try:
            user = self.auth.login(self.txt_user.text(), self.txt_pass.text())
            if user:
                if user.trocar_senha: ChangePasswordDialog(self.auth, user.id, lambda: self.on_success(user)).exec(); self.close()
                else: self.on_success(user)
            else: QMessageBox.warning(self, "Erro", "Login inválido."); self.logging_in = False
        except Exception as e: self.logging_in = False; QMessageBox.critical(self, "Erro", str(e))
    def open_register(self): reg = RegisterWindow(self.auth, self); reg.exec()

# --- USUÁRIO COMUM ---
class UserWindow(QMainWindow): 
    def __init__(self, user, chamado_controller, logout_callback):
        super().__init__()
        self.user = user
        self.controller = chamado_controller
        self.logout_callback = logout_callback
        self.setWindowTitle(f"Painel - {user.nome}")
        
        # TELA CHEIA
        self.setup_ui()
        self.switch_page(1)
        QTimer.singleShot(100, self.showMaximized)

    def setup_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        sidebar = QWidget()
        sidebar.setObjectName("Sidebar")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setAlignment(Qt.AlignTop)
        
        lbl_brand = QLabel("SisCall")
        lbl_brand.setObjectName("MenuTitle")
        lbl_brand.setAlignment(Qt.AlignCenter)
        
        self.btn_new_ticket = QPushButton("Novo Chamado")
        self.btn_new_ticket.setObjectName("MenuBtn")
        self.btn_new_ticket.setIcon(QIcon.fromTheme("list-add"))
        self.btn_new_ticket.setCheckable(True)
        self.btn_new_ticket.clicked.connect(lambda: self.switch_page(0))

        self.btn_my_tickets = QPushButton("Meus Chamados")
        self.btn_my_tickets.setObjectName("MenuBtn")
        self.btn_my_tickets.setIcon(QIcon.fromTheme("folder-documents"))
        self.btn_my_tickets.setCheckable(True)
        self.btn_my_tickets.clicked.connect(lambda: self.switch_page(1))

        btn_logout = QPushButton("Sair")
        btn_logout.setObjectName("MenuBtn")
        btn_logout.setStyleSheet("color: #ff6b6b;")
        btn_logout.clicked.connect(self.logout_callback)

        sidebar_layout.addWidget(lbl_brand)
        sidebar_layout.addSpacing(20)
        sidebar_layout.addWidget(self.btn_new_ticket)
        sidebar_layout.addWidget(self.btn_my_tickets)
        sidebar_layout.addStretch()
        sidebar_layout.addWidget(btn_logout)

        self.pages = QStackedWidget()
        self.page_new = self.create_open_ticket_page()
        self.page_list = self.create_my_tickets_page()
        
        self.pages.addWidget(self.page_new)
        self.pages.addWidget(self.page_list)

        main_layout.addWidget(sidebar)
        main_layout.addWidget(self.pages)

    def create_open_ticket_page(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignTop)
        
        header = QLabel("Abrir Novo Chamado")
        header.setStyleSheet("font-size: 24px; font-weight: bold; color: #2c3e50; margin: 10px 0;")
        
        form_frame = QWidget()
        # RESTAURAÇÃO DO ESTILO CORRETO DO FRAME PARA NÃO QUEBRAR O BOTÃO
        form_frame.setObjectName("TicketFormFrame")
        form_frame.setStyleSheet("""
            #TicketFormFrame { background-color: white; border-radius: 6px; border: 1px solid #ddd; }
            QLabel { color: #333333; background-color: transparent; border: none; }
        """)
        
        form_layout = QVBoxLayout(form_frame)
        form_layout.setSpacing(15)

        form_layout.addWidget(QLabel("Máquina / Dispositivo:"))
        self.combo_machine = QComboBox()
        self.combo_machine.addItems([
            "COMPUTADOR",
            "NOTEBOOK",
            "IMPRESSORA",
            "TELEFONE",
            "INTERNET",
            "SCANNER",
            "Solicitação de Criação de Conta",  # NOVA OPÇÃO
            "Outro Dispositivo"
        ])
        # Conectar mudança de seleção para mostrar/ocultar checkboxes
        self.combo_machine.currentIndexChanged.connect(self.on_machine_changed)
        form_layout.addWidget(self.combo_machine)

        # CONTAINER PARA OS CHECKBOXES DE CONTAS (INICIALMENTE OCULTO)
        self.contas_container = QWidget()
        self.contas_layout = QVBoxLayout(self.contas_container)
        self.contas_layout.setSpacing(8)
        
        # Label do container
        self.contas_label = QLabel("Selecione os sistemas que precisa de conta:")
        self.contas_label.setStyleSheet("color: #2c3e50; font-weight: bold;")
        
        # Checkboxes de sistemas disponíveis
        # Sistemas internos que podem ter contas criadas
        self.checkboxes_contas = {}
        sistemas = ["Email Corporativo", "SharePoint", "Confluence", "Jira", "GitHub", "VPN", "Servidor Interno"]
        
        for sistema in sistemas:
            cb = QCheckBox(sistema)
            cb.setStyleSheet("QCheckBox { color: #333; background-color: transparent; }")
            self.checkboxes_contas[sistema] = cb
            self.contas_layout.addWidget(cb)
        
        self.contas_container.setVisible(False)  # Inicialmente oculto
        form_layout.addWidget(self.contas_label)
        form_layout.addWidget(self.contas_container)

        form_layout.addWidget(QLabel("Descrição do Problema:"))
        self.txt_desc = QPlainTextEdit()
        self.txt_desc.setPlaceholderText("Descreva detalhadamente o erro...")
        self.txt_desc.setMinimumHeight(150)
        self.txt_desc.setStyleSheet("border: 1px solid #ccc; background-color: white; color: #333;")
        form_layout.addWidget(self.txt_desc)

        btn_submit = QPushButton("Enviar Solicitação")
        btn_submit.setMinimumHeight(45)
        btn_submit.setObjectName("SubmitBtn")
        btn_submit.clicked.connect(self.criar_chamado)
        form_layout.addWidget(btn_submit)

        layout.addWidget(header)
        layout.addWidget(form_frame)
        layout.addStretch()
        return widget

    def on_machine_changed(self):
        """Mostra/oculta checkboxes de contas quando seleção muda"""
        is_conta = self.combo_machine.currentText() == "Solicitação de Criação de Conta"
        self.contas_label.setVisible(is_conta)
        self.contas_container.setVisible(is_conta)
        
        # Se não é conta, limpar checkboxes
        if not is_conta:
            for cb in self.checkboxes_contas.values():
                cb.setChecked(False)

    def create_my_tickets_page(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        header = QLabel(f"Histórico de Chamados")
        header.setStyleSheet("font-size: 24px; font-weight: bold; color: #2c3e50; margin: 10px 0;")
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setColumnCount(7) # Agora 7 colunas (Hora+Data)
        self.table.setHorizontalHeaderLabels(["ID", "Hora", "Data", "Máquina", "Descrição", "Status", "Ação"])
        
        self.table.setColumnWidth(0, 40) 
        self.table.setColumnWidth(1, 90) 
        self.table.setColumnWidth(2, 90)
        self.table.setColumnWidth(3, 200)
        self.table.setColumnWidth(5, 120)
        self.table.setColumnWidth(6, 150)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.verticalHeader().setVisible(False) 
        
        # Aumentar altura da linha para acomodar botões confortavelmente
        self.table.verticalHeader().setMinimumSectionSize(70)
        self.table.verticalHeader().setDefaultSectionSize(70)
        
        self.table.setWordWrap(True)
        layout.addWidget(header)
        layout.addWidget(self.table)
        return widget

    def switch_page(self, index):
        self.pages.setCurrentIndex(index)
        self.btn_new_ticket.setChecked(index == 0)
        self.btn_my_tickets.setChecked(index == 1)
        if index == 1: self.load_data()

    def load_data(self):
        try:
            chamados = self.controller.listar_meus_chamados(self.user.id)
            self.preencher_tabela(self.table, chamados, is_admin=False)
        except Exception as e: print(f"Erro load_data: {e}")

    def preencher_tabela(self, table, chamados, is_admin=False):
        def parse_date(date_str):
            try: return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
            except: return None
        table.setRowCount(len(chamados))
        for i, c in enumerate(chamados):
            id_item = QTableWidgetItem(str(c.id)); id_item.setTextAlignment(Qt.AlignCenter); table.setItem(i, 0, id_item)
            
            dt = parse_date(c.data_abertura)
            hora, data = ("", c.data_abertura)
            if dt: hora, data = dt.strftime('%H:%M'), dt.strftime('%d/%m/%y')
            
            h_item = QTableWidgetItem(hora); h_item.setTextAlignment(Qt.AlignCenter); table.setItem(i, 1, h_item)
            d_item = QTableWidgetItem(data); d_item.setTextAlignment(Qt.AlignCenter); table.setItem(i, 2, d_item)
            table.setItem(i, 3, QTableWidgetItem(c.maquina or "N/A"))
            table.setItem(i, 4, QTableWidgetItem(c.descricao))
            status_item = QTableWidgetItem(c.status); status_item.setTextAlignment(Qt.AlignCenter)
            font = QFont(); font.setBold(True); status_item.setFont(font)
            if c.status == "Aberto": status_item.setForeground(QColor("#d32f2f"))#cor do status aberto pagina user
            elif c.status == "Finalizado": status_item.setForeground(QColor("#2E7D32"))#cor do status fechado pagina user
            else: status_item.setForeground(QColor("#F57C00"))#cor do status em andamento pagina user
            table.setItem(i, 5, status_item)
            
            if not is_admin:
                if c.status == "Aberto":
                    btn_del = QPushButton("Excluir"); btn_del.setObjectName("Danger")
                    btn_del.setFixedSize(80, 30)
                    btn_del.clicked.connect(lambda _, cid=c.id: self.deletar_chamado(cid))
                    cell = QWidget(); l = QHBoxLayout(cell); l.setContentsMargins(5,5,5,5); l.addWidget(btn_del); table.setCellWidget(i, 6, cell)
                else: table.setCellWidget(i, 6, QWidget())

    def criar_chamado(self):
        try:
            maquina = self.combo_machine.currentText()
            descricao = self.txt_desc.toPlainText()
            
            # Se for solicitação de conta, validar se selecionou ao menos uma
            if maquina == "Solicitação de Criação de Conta":
                contas_selecionadas = [sistema for sistema, cb in self.checkboxes_contas.items() if cb.isChecked()]
                if not contas_selecionadas:
                    QMessageBox.warning(self, "Erro", "Selecione pelo menos um sistema para criação de conta!")
                    return
                # Converter para string (separada por vírgula)
                contas_str = ", ".join(contas_selecionadas)
                # Passar contas_selecionadas para controller
                self.controller.criar_chamado_com_contas(self.user.id, descricao, maquina, contas_str)
            else:
                # Chamado normal (sem contas)
                self.controller.criar_chamado(self.user.id, descricao, maquina)
            
            QMessageBox.information(self, "Sucesso", "Chamado registrado!")
            self.txt_desc.clear()
            self.combo_machine.setCurrentIndex(0)
            # Limpar checkboxes
            for cb in self.checkboxes_contas.values():
                cb.setChecked(False)
            self.switch_page(1)
        except Exception as e:
            QMessageBox.warning(self, "Erro", str(e))

    def deletar_chamado(self, chamado_id):
        confirm = QMessageBox.question(self, "Confirmar", "Excluir?", QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            try: self.controller.excluir_chamado(chamado_id); self.load_data()
            except Exception as e: QMessageBox.warning(self, "Erro", str(e))

# --- ADMIN WINDOW (MAXIMIZADO + RELATÓRIOS + GESTÃO) ---
class AdminWindow(QMainWindow): 
    def __init__(self, user, chamado_controller, logout_callback):
        super().__init__()
        self.user = user
        self.controller = chamado_controller
        self.logout_callback = logout_callback
        self.setWindowTitle("Gestão de Chamados - Admin")
        self.setup_ui()
        QTimer.singleShot(100, self.showMaximized) 
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_data)
        self.timer.start(1000) 
        self.refresh_data()

    def set_auth_controller(self, auth_controller):
        self.auth_controller = auth_controller

    def setup_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        sidebar = QWidget()
        sidebar.setObjectName("Sidebar")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setAlignment(Qt.AlignTop)
        lbl_brand = QLabel("SisCall")
        lbl_brand.setObjectName("MenuTitle")
        lbl_brand.setAlignment(Qt.AlignCenter)
        
        self.btn_work = QPushButton("Tarefas"); self.btn_work.setObjectName("MenuBtn"); self.btn_work.setIcon(QIcon.fromTheme("view-list")); self.btn_work.setCheckable(True); self.btn_work.setChecked(True); self.btn_work.clicked.connect(lambda: self.switch_page(0))
        self.btn_all = QPushButton("Histórico"); self.btn_all.setObjectName("MenuBtn"); self.btn_all.setIcon(QIcon.fromTheme("x-office-spreadsheet")); self.btn_all.setCheckable(True); self.btn_all.clicked.connect(lambda: self.switch_page(1))
        
        # NOVO: Botão Relatórios
        self.btn_reports = QPushButton("Relatórios"); self.btn_reports.setObjectName("MenuBtn"); self.btn_reports.setCheckable(True); self.btn_reports.clicked.connect(lambda: self.switch_page(2))
        
        self.btn_config = QPushButton("Configurações"); self.btn_config.setObjectName("MenuBtn"); self.btn_config.setIcon(QIcon.fromTheme("preferences-system")); self.btn_config.setCheckable(True); self.btn_config.clicked.connect(lambda: self.switch_page(3))
        btn_logout = QPushButton("Sair"); btn_logout.setObjectName("MenuBtn"); btn_logout.setStyleSheet("color: #ff6b6b;"); btn_logout.clicked.connect(self.logout_callback)

        sidebar_layout.addWidget(lbl_brand); sidebar_layout.addSpacing(20); sidebar_layout.addWidget(self.btn_work); sidebar_layout.addWidget(self.btn_all); sidebar_layout.addWidget(self.btn_reports); sidebar_layout.addWidget(self.btn_config); sidebar_layout.addStretch(); sidebar_layout.addWidget(btn_logout)

        self.pages = QStackedWidget()
        self.page_work = self.create_table_page("Chamados Pendentes", edit_mode=True)
        self.page_all = self.create_table_page("Histórico Completo", edit_mode=False)
        self.page_reports = self.create_reports_page()
        self.page_config_widget = self.create_config_page()

        self.pages.addWidget(self.page_work['widget'])
        self.pages.addWidget(self.page_all['widget'])
        self.pages.addWidget(self.page_reports)
        self.pages.addWidget(self.page_config_widget)

        main_layout.addWidget(sidebar)
        main_layout.addWidget(self.pages)

    def create_table_page(self, title_text, edit_mode):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        header = QLabel(title_text)
        header.setStyleSheet("font-size: 24px; font-weight: bold; color: #2c3e50; margin: 15px 5px;")
        table = QTableWidget()
        table.setAlternatingRowColors(True)
        # 9 Colunas (Hora e Data separadas)
        cols = ["ID", "Setor", "Usuário", "Máquina", "Hora", "Data", "Descrição", "Status", "Ação"]
        if not edit_mode: cols = ["ID", "Setor", "Usuário", "Máquina", "Hora", "Data", "Descrição", "Status", "Responsável"]
        table.setColumnCount(len(cols))
        table.setHorizontalHeaderLabels(cols)
        
        table.setColumnWidth(0, 40)
        table.setColumnWidth(1, 150)
        table.setColumnWidth(2, 150)
        table.setColumnWidth(3, 120)
        table.setColumnWidth(4, 90)
        table.setColumnWidth(5, 90)
        table.setColumnWidth(7, 150) 
        table.setColumnWidth(8, 200)
        table.horizontalHeader().setSectionResizeMode(6, QHeaderView.Stretch) # Descrição
        
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.verticalHeader().setVisible(False) 
        # Altura minima para caber o botão
        table.verticalHeader().setMinimumSectionSize(70)
        table.verticalHeader().setDefaultSectionSize(70)
        table.setWordWrap(True)
        layout.addWidget(header); layout.addWidget(table)
        return {'widget': widget, 'table': table, 'edit_mode': edit_mode}

    # --- RELATÓRIOS ---
    def create_reports_page(self):
        widget = QWidget(); layout = QVBoxLayout(widget); layout.setAlignment(Qt.AlignTop)
        header = QLabel("Relatórios Gerenciais"); header.setStyleSheet("font-size: 24px; font-weight: bold; color: #2c3e50; margin: 15px 5px;")
        layout.addWidget(header)
        
        filter_frame = QFrame(); filter_frame.setStyleSheet("background: white; border-radius: 5px; padding: 10px;")
        fl = QHBoxLayout(filter_frame)
        self.date_inicio = QDateEdit(); self.date_inicio.setCalendarPopup(True); self.date_inicio.setDate(QDate.currentDate().addDays(-30))
        self.date_fim = QDateEdit(); self.date_fim.setCalendarPopup(True); self.date_fim.setDate(QDate.currentDate())
        btn_gerar = QPushButton("Gerar Relatório"); btn_gerar.setFixedSize(150, 36); btn_gerar.clicked.connect(self.gerar_relatorios)
        btn_gerar.setStyleSheet('background:#2c3e50; color: white;')
        fl.addWidget(QLabel("De:")); fl.addWidget(self.date_inicio); fl.addWidget(QLabel("Até:")); fl.addWidget(self.date_fim); fl.addWidget(btn_gerar); fl.addStretch()
        layout.addWidget(filter_frame)

        self.grid_metrics = QGridLayout()
        self.card_setor = self.create_metric_card("Setor com mais chamados", "-", "0")
        self.card_maquina = self.create_metric_card("Máquina mais problemática", "-", "0")
        self.card_suporte = self.create_metric_card("Suporte mais produtivo", "-", "0")
        self.card_tempo = self.create_metric_card("Tempo médio de resolução", "-", "Horas")
        self.grid_metrics.addWidget(self.card_setor, 0, 0); self.grid_metrics.addWidget(self.card_maquina, 0, 1); self.grid_metrics.addWidget(self.card_suporte, 1, 0); self.grid_metrics.addWidget(self.card_tempo, 1, 1)
        layout.addLayout(self.grid_metrics); layout.addStretch()
        return widget

    def create_metric_card(self, title, main_value, sub_value):
        box = QGroupBox(title); l = QVBoxLayout(box)
        val = QLabel(main_value); val.setObjectName("MetricValue"); val.setAlignment(Qt.AlignCenter)
        sub = QLabel(sub_value); sub.setObjectName("MetricLabel"); sub.setAlignment(Qt.AlignCenter)
        l.addWidget(val); l.addWidget(sub); return box

    def update_card(self, box, value, sub):
        box.findChild(QLabel, "MetricValue").setText(str(value))
        box.findChild(QLabel, "MetricLabel").setText(str(sub))

    def gerar_relatorios(self):
        d_ini = self.date_inicio.date().toString("yyyy-MM-dd"); d_fim = self.date_fim.date().toString("yyyy-MM-dd")
        try:
            data = self.controller.gerar_relatorio(d_ini, d_fim)
            self.update_card(self.card_setor, data["top_setor"][0], f"{data['top_setor'][1]} chamados")
            self.update_card(self.card_maquina, data["top_maquina"][0], f"{data['top_maquina'][1]} problemas")
            self.update_card(self.card_suporte, data["top_suporte"][0], f"{data['top_suporte'][1]} resolvidos")
            self.update_card(self.card_tempo, data["tempo_medio"], "Médio")
        except Exception as e: QMessageBox.warning(self, "Erro", f"Falha ao gerar: {e}")

    # --- CONFIG (GESTÃO DE USUÁRIOS) ---
    def create_config_page(self):
        widget = QWidget(); layout = QVBoxLayout(widget); layout.setAlignment(Qt.AlignTop)
        header = QLabel("Gestão de Usuários")
        header.setStyleSheet("font-size: 24px; font-weight: bold; color: #2c3e50; margin: 15px 5px;")
        layout.addWidget(header)
        filter_layout = QHBoxLayout()
        self.txt_search_user = QLineEdit(); self.txt_search_user.setPlaceholderText("Buscar por Nome ou Login...")
        self.txt_search_user.textChanged.connect(self.load_users)
        self.combo_filter_setor = QComboBox(); self.combo_filter_setor.addItems(["Todos", "Administrativo", "Comercial / Vendas", "Financeiro", "Recursos Humanos (RH)", "TI - Desenvolvimento", "TI - Infraestrutura", "Operacional / Logística", "Jurídico", "Marketing"])
        self.combo_filter_setor.currentTextChanged.connect(self.load_users)
        filter_layout.addWidget(self.txt_search_user); filter_layout.addWidget(self.combo_filter_setor); layout.addLayout(filter_layout)
        
        self.table_users = QTableWidget()
        self.table_users.setAlternatingRowColors(True)
        self.table_users.setColumnCount(5)
        self.table_users.setHorizontalHeaderLabels(["ID", "Nome", "Login", "Setor", "Ações"])
        
        # CONFIGURAÇÃO ROBUSTA DA TABELA DE USUÁRIOS
        self.table_users.setColumnWidth(0, 60)
        self.table_users.setColumnWidth(2, 150)
        self.table_users.setColumnWidth(3, 200)
        self.table_users.setColumnWidth(4, 320) # Ações bem largas
        self.table_users.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        
        self.table_users.verticalHeader().setMinimumSectionSize(70) # Altura min
        self.table_users.verticalHeader().setDefaultSectionSize(70) # Altura padrão
        self.table_users.verticalHeader().setVisible(False)
        self.table_users.setEditTriggers(QAbstractItemView.NoEditTriggers)
        
        layout.addWidget(self.table_users)
        return widget

    def switch_page(self, index):
        self.pages.setCurrentIndex(index)
        self.btn_work.setChecked(index == 0)
        self.btn_all.setChecked(index == 1)
        self.btn_reports.setChecked(index == 2)
        self.btn_config.setChecked(index == 3)
        if index == 3: self.load_users()
        elif index == 2: pass
        else: self.refresh_data()

    def load_users(self):
        if not hasattr(self, 'auth_controller'): return
        termo = self.txt_search_user.text(); setor = self.combo_filter_setor.currentText()
        usuarios = self.auth_controller.listar_usuarios(termo, setor)
        self.table_users.setRowCount(len(usuarios))
        for i, u in enumerate(usuarios):
            self.table_users.setItem(i, 0, QTableWidgetItem(str(u.id)))
            nome_display = u.nome + (" (Admin)" if u.tipo == 1 else "")
            self.table_users.setItem(i, 1, QTableWidgetItem(nome_display))
            self.table_users.setItem(i, 2, QTableWidgetItem(u.login))
            self.table_users.setItem(i, 3, QTableWidgetItem(u.setor or "-"))
            
            # Botões de Gestão
            btn_edit = QPushButton("Editar"); btn_edit.setFixedSize(90, 36)
            btn_edit.clicked.connect(lambda _, user=u: self.editar_usuario(user))
            btn_del = QPushButton("Excluir"); btn_del.setObjectName("Danger"); btn_del.setFixedSize(90, 36)
            btn_del.clicked.connect(lambda _, uid=u.id: self.excluir_usuario(uid))
            
            container = QWidget(); l = QHBoxLayout(container); l.setContentsMargins(2,2,2,2)
            l.addWidget(btn_edit); l.addWidget(btn_del); self.table_users.setCellWidget(i, 4, container)

    def editar_usuario(self, user):
        dialog = UserEditDialog(self.auth_controller, user, self)
        dialog.exec()
        self.load_users()

    def excluir_usuario(self, user_id):
        confirm = QMessageBox.question(self, "Excluir", "Tem certeza?", QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            try: self.auth_controller.excluir_usuario(user_id); self.load_users()
            except Exception as e: QMessageBox.warning(self, "Erro", str(e))

    def refresh_data(self):
        current_idx = self.pages.currentIndex()
        try:
            if current_idx == 0:
                chamados = self.controller.listar_pendentes()
                self.preencher_tabela_admin(self.page_work['table'], chamados, edit_mode=True)
            elif current_idx == 1:
                chamados = self.controller.listar_todos()
                self.preencher_tabela_admin(self.page_all['table'], chamados, edit_mode=False)
        except Exception as e: print(f"Erro refresh: {e}")

    def preencher_tabela_admin(self, table, chamados, edit_mode):
        v_scroll = table.verticalScrollBar().value()
        table.setRowCount(len(chamados))
        def parse_date(date_str):
            try: return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
            except: return None
        agora = datetime.now()
        for i, c in enumerate(chamados):
            # Lógica de Piscar
            dt_obj = parse_date(c.data_abertura)
            bg_color = None; fg_color = None; border_style = ""
            if dt_obj:
                diff = (agora - dt_obj).total_seconds()
                if diff < 16:
                    cycle = diff % 4 
                    if cycle < 2: bg_color = QColor("#d32f2f"); fg_color = QColor("white")
                    else: bg_color = QColor("white"); fg_color = QColor("#d32f2f"); border_style = "border: 1px solid #d32f2f;"
            
            # Dados
            id_item = QTableWidgetItem(str(c.id)); table.setItem(i, 0, id_item)
            table.setItem(i, 1, QTableWidgetItem(c.setor_usuario))
            table.setItem(i, 2, QTableWidgetItem(c.nome_usuario))
            table.setItem(i, 3, QTableWidgetItem(c.maquina or "N/A"))
            
            # Hora e Data Separados
            dt = parse_date(c.data_abertura)
            hora, data = ("", c.data_abertura)
            if dt: hora, data = dt.strftime('%H:%M'), dt.strftime('%d/%m/%y')
            h_item = QTableWidgetItem(hora); h_item.setTextAlignment(Qt.AlignCenter); table.setItem(i, 4, h_item)
            d_item = QTableWidgetItem(data); d_item.setTextAlignment(Qt.AlignCenter); table.setItem(i, 5, d_item)
            
            table.setItem(i, 6, QTableWidgetItem(c.descricao))
            status_item = QTableWidgetItem(c.status); status_item.setTextAlignment(Qt.AlignCenter)
            font = QFont(); font.setBold(True); status_item.setFont(font)
            if c.status == "Aberto": status_item.setForeground(QColor("#d32f2f"))
            elif c.status == "Finalizado": status_item.setForeground(QColor("#2E7D32"))
            else: status_item.setForeground(QColor("#F57C00"))
            table.setItem(i, 7, status_item)
            
            if edit_mode:
                btn = QPushButton(); btn.setFixedSize(130, 36)
                is_mine = (c.suporte_id == self.user.id)
                is_locked = (c.status == "Em andamento" and not is_mine)
                if c.status == "Aberto": btn.setText("Atender"); btn.setObjectName("Info"); btn.setEnabled(True)
                elif is_locked: btn.setText("Bloqueado"); btn.setEnabled(False)
                else: btn.setText("Continuar"); btn.setObjectName("SubmitBtn"); btn.setEnabled(True)
                if not is_locked: btn.clicked.connect(lambda _, cid=c.id: self.abrir_atendimento(cid))
                
                # Aplica estilo piscante APENAS no botão
                widget = QWidget(); layout = QHBoxLayout(widget); layout.setContentsMargins(5, 5, 5, 5); layout.addWidget(btn)
                if bg_color:
                    bg_hex = bg_color.name(); fg_hex = fg_color.name()
                    widget.setStyleSheet(f"background-color: transparent;")
                    btn.setStyleSheet(f"background-color: {bg_hex}; color: {fg_hex}; {border_style} border-radius: 4px; font-weight: bold;")
                
                table.setCellWidget(i, 8, widget)
            else: table.setItem(i, 8, QTableWidgetItem(c.nome_suporte or "-"))
        table.verticalScrollBar().setValue(v_scroll)

    def abrir_atendimento(self, chamado_id):
        self.timer.stop()
        dialog = TicketActionDialog(chamado_id, self.controller, self.user, self)
        dialog.exec()
        self.timer.start(1000)
        self.refresh_data()