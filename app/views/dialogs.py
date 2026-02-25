# views/dialogs.py
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QComboBox, QPushButton, 
    QLineEdit, QMessageBox, QScrollArea, QWidget, QFrame, QPlainTextEdit
)
from PySide6.QtCore import Qt
from .common import CenterMixin

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
        self.combo_tipo.addItems(["Usuário", "Administrador", "Responsável"])
        # 0=User, 1=Admin, 2=Responsável
        self.combo_tipo.setCurrentIndex(self.user.tipo if self.user.tipo in [0, 1, 2] else 0)
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
            novo_tipo = self.combo_tipo.currentIndex()
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

# --- DIALOGO DE CADASTRO DE USUÁRIO (ADMIN) ---
class UserRegisterDialog(QDialog, CenterMixin):
    def __init__(self, auth_controller, parent=None):
        super().__init__(parent)
        self.auth = auth_controller
        self.setWindowTitle("Cadastrar Novo Usuário")
        self.setFixedSize(400, 550)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        self.txt_nome = QLineEdit(); self.txt_nome.setPlaceholderText("Nome")
        layout.addWidget(QLabel("Nome:")); layout.addWidget(self.txt_nome)

        self.txt_sobrenome = QLineEdit(); self.txt_sobrenome.setPlaceholderText("Sobrenome")
        layout.addWidget(QLabel("Sobrenome:")); layout.addWidget(self.txt_sobrenome)

        self.txt_login = QLineEdit(); self.txt_login.setPlaceholderText("Login")
        layout.addWidget(QLabel("Login:")); layout.addWidget(self.txt_login)

        self.txt_senha = QLineEdit(); self.txt_senha.setPlaceholderText("Senha"); self.txt_senha.setEchoMode(QLineEdit.Password)
        layout.addWidget(QLabel("Senha:")); layout.addWidget(self.txt_senha)

        layout.addWidget(QLabel("Setor:"))
        self.combo_setor = QComboBox()
        self.combo_setor.addItems(["Selecione seu Setor", "GERH", "ASCOM", "COTRANSP", "GEATEC", "GEINFORM", "GECONF", "GEAAD", "PROJUR", "DIRAF","DITEC","AGEPLAN","PRESIDENCIA","OUVIDORIA","PROTOCOLO","AUDITORIO","LABAGUA","CONSEGER","GEMETRO","GEREMETRO","COMEL","AGEQUALI","CPI","ARRECADAÇÂO","FISCAIS","LABAGUA","LEI","LABORG","LABROMO","LABSOLOS","LABMICRO","PRE-MEDIDOS","GUARITA"])
        layout.addWidget(self.combo_setor)

        layout.addWidget(QLabel("Cargo:"))
        self.combo_tipo = QComboBox()
        self.combo_tipo.addItems(["Usuário", "Administrador", "Responsável"])
        layout.addWidget(self.combo_tipo)

        btn_save = QPushButton("Cadastrar")
        btn_save.setObjectName("SubmitBtn")
        btn_save.clicked.connect(self.cadastrar)
        layout.addWidget(btn_save)

    def cadastrar(self):
        try:
            tipo_map = {"Usuário": 0, "Administrador": 1, "Responsável": 2}
            tipo_sel = tipo_map.get(self.combo_tipo.currentText(), 0)
            
            self.auth.cadastrar_usuario(
                self.txt_nome.text(),
                self.txt_sobrenome.text(),
                self.txt_login.text(),
                self.txt_senha.text(),
                self.combo_setor.currentText(),
                tipo=tipo_sel
            )
            QMessageBox.information(self, "Sucesso", "Usuário cadastrado com sucesso!")
            self.accept()
        except Exception as e:
            QMessageBox.warning(self, "Erro", str(e))

# --- JANELA DE AÇÃO DE SOLICITAÇÃO DE CONTA ---
class AccountRequestActionDialog(QDialog, CenterMixin):
    def __init__(self, solicitacao_id, controller, user_suporte, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.solicitacao_id = solicitacao_id
        self.user_suporte = user_suporte
        self.setWindowTitle(f"Atendimento Solicitação de Conta #{solicitacao_id}")
        self.setStyleSheet("background-color: #fdfdfd; color: #333333;")
        self.setup_ui()
        self.load_solicitacao()

    def setup_ui(self):
        s = self.controller.buscar_por_id(self.solicitacao_id)
        if s.status == "Aberto": self.setFixedSize(600,500)
        else: self.setFixedSize(600,700)
        self.layout = QVBoxLayout(self)
        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setStyleSheet("background-color: #fdfdfd; border: none;") 
        scroll_content = QWidget(); scroll_content.setStyleSheet("background-color: #fdfdfd;")
        self.details_layout = QVBoxLayout(scroll_content)
        self.lbl_info = QLabel(); self.lbl_info.setStyleSheet("font-size: 15px; line-height: 1.5; color: #333;"); self.lbl_info.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.details_layout.addWidget(self.lbl_info); self.details_layout.addSpacing(10)
        scroll.setWidget(scroll_content)
        self.layout.addWidget(scroll)
        self.action_frame = QFrame(); self.action_frame.setStyleSheet("QFrame { background-color: #C4CFED; border-radius: 5px; padding: 10px; border: 1px solid #9DA2AE; } QLabel { color: #333; }")
        self.action_layout = QVBoxLayout(self.action_frame)
        self.layout.addWidget(self.action_frame)

    def load_solicitacao(self):
        s = self.controller.buscar_por_id(self.solicitacao_id)
        if not s: self.close(); return
        
        info_text = f"""
        <h3 style='margin:0; color:#2c3e50;'>{s.nome_usuario}</h3>
        <span style='color:#7f8c8d;'>{s.setor_usuario}</span><br><br>
        <b>Aberto em:</b> {s.data_abertura}<br>
        <b>Status:</b> <b style='font-size:16px; color:{'red' if s.status=='Aberto' else 'blue'}'>{s.status.upper()}</b><br>
        <hr>
        <b>Sistemas Solicitados:</b><br>
        <div style='background-color:#e8f4f8; padding:10px; border-radius:4px; border:1px solid #add8e6; color: #333;'>
        {s.sistemas_solicitados.replace(',', '<br>')}
        </div>
        """
        if s.descricao:
            info_text += f"<br><b>Observações:</b><br><div style='background-color:#fff; padding:10px; border-radius:4px; border:1px solid #ddd; color: #333;'>{s.descricao}</div>"

        self.lbl_info.setText(info_text)
        while self.action_layout.count():
            child = self.action_layout.takeAt(0)
            if child.widget(): child.widget().deleteLater()

        if s.status == "Aberto": self.build_start_ui()
        elif s.status == "Em andamento":
            if s.suporte_id == self.user_suporte.id: self.build_finish_ui(s)
            else: self.build_locked_ui(s)
        else: self.build_readonly_ui(s)

    def build_start_ui(self):
        lbl = QLabel("Esta solicitação está aguardando atendimento.")
        btn_start = QPushButton("Iniciar Atendimento"); btn_start.setObjectName("SubmitBtn")
        btn_start.clicked.connect(self.iniciar_atendimento)
        self.action_layout.addWidget(lbl); self.action_layout.addWidget(btn_start)

    def build_finish_ui(self, solicitacao):
        lbl = QLabel(f"<b>Em atendimento desde:</b> {solicitacao.data_inicio_atendimento}")
        btn_finish = QPushButton("Finalizar Solicitação"); btn_finish.setObjectName("SubmitBtn")
        btn_finish.clicked.connect(self.finalizar_atendimento)
        
        self.action_layout.addWidget(lbl)
        self.action_layout.addWidget(QLabel("Credenciais Criadas:"))
        self.txt_credenciais = QPlainTextEdit()
        self.txt_credenciais.setPlaceholderText("Digite o login e senha separados por | (exemplo: usuario.nome | senha123)")
        self.txt_credenciais.setStyleSheet("background-color: white; color: #333;")
        self.action_layout.addWidget(self.txt_credenciais)
        self.action_layout.addWidget(btn_finish)

    def build_locked_ui(self, solicitacao):
        lbl = QLabel(f"Esta solicitação já está sendo atendida por <b>{solicitacao.nome_suporte}</b>.")
        self.action_layout.addWidget(lbl)

    def build_readonly_ui(self, solicitacao):
        info = f"<b>Responsável:</b> {solicitacao.nome_suporte}<br><b>Início:</b> {solicitacao.data_inicio_atendimento} | <b>Fim:</b> {solicitacao.data_fechamento}<br><br><b>Credenciais Criadas:</b><br><div style='background-color:#e8f4f8; padding:10px; border-radius:4px; border:1px solid #add8e6; color: #333;'>{solicitacao.credenciais_criadas}</div>"
        lbl = QLabel(info); lbl.setWordWrap(True)
        self.action_layout.addWidget(lbl)

    def iniciar_atendimento(self):
        try: 
            self.controller.assumir_solicitacao(self.solicitacao_id, self.user_suporte.id)
            QMessageBox.information(self, "Sucesso", "Solicitação em execução!")
            self.load_solicitacao()
        except Exception as e: QMessageBox.warning(self, "Erro", str(e))

    def finalizar_atendimento(self):
        try:
            self.controller.finalizar_solicitacao(self.solicitacao_id, self.user_suporte.id, self.txt_credenciais.toPlainText())
            QMessageBox.information(self, "Sucesso", "Solicitação finalizada!")
            self.accept()
        except Exception as e:
            QMessageBox.warning(self, "Erro", str(e))

# --- JANELA DE AÇÃO DO SUPORTE ---
class TicketActionDialog(QDialog, CenterMixin):
    def __init__(self, chamado_id, controller, user_suporte, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.chamado_id = chamado_id
        self.user_suporte = user_suporte
        self.setWindowTitle(f"Atendimento Chamado #{chamado_id}")
        self.setStyleSheet("background-color: #fdfdfd; color: #333333;")
        self.setup_ui()
        self.load_chamado()

    def setup_ui(self):
        c = self.controller.buscar_por_id(self.chamado_id)
        if c.status == "Aberto": self.setFixedSize(600,500)
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
        btn_finish = QPushButton("Marcar como Resolvido")
        btn_finish.setObjectName("SubmitBtn")
        btn_finish.clicked.connect(self.resolver_atendimento)
        
        self.action_layout.addWidget(lbl)
        
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

    def build_locked_ui(self, chamado):
        lbl = QLabel(f"Este chamado já está sendo atendido por <b>{chamado.nome_suporte}</b>.")
        self.action_layout.addWidget(lbl)
    
    def build_readonly_ui(self, chamado):
        info = f"<b>Responsável:</b> {chamado.nome_suporte}<br><b>Início:</b> {chamado.data_inicio_atendimento} | <b>Fim:</b> {chamado.data_fechamento}<br><br><b>Diagnóstico:</b> {chamado.diagnostico}<br><b>Solução:</b> {chamado.solucao}"
        lbl = QLabel(info); lbl.setWordWrap(True)
        self.action_layout.addWidget(lbl)

    def iniciar_atendimento(self):
        try: 
            self.controller.assumir_chamado(self.chamado_id, self.user_suporte.id)
            QMessageBox.information(self, "Sucesso", "Chamado em execução!")
            self.load_chamado()
        except Exception as e: QMessageBox.warning(self, "Erro", str(e))

    def resolver_atendimento(self):
        try:
            self.controller.resolver_chamado(self.chamado_id, self.user_suporte.id, self.txt_diag.toPlainText(), self.txt_solucao.toPlainText())
            QMessageBox.information(self, "Sucesso", "Chamado marcado como resolvido! Aguardando confirmação do usuário.")
            self.accept()
        except Exception as e:
            QMessageBox.warning(self, "Erro", str(e))