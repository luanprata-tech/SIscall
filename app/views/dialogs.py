# views/dialogs.py
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QComboBox, QPushButton, 
    QLineEdit, QMessageBox, QScrollArea, QWidget, QFrame, QPlainTextEdit,
    QGridLayout
)
from PySide6.QtCore import Qt
from .common import CenterMixin, LISTA_SETORES
import json

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
        self.combo_setor.addItems(LISTA_SETORES)
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
        itens_setor = ["Selecione seu Setor"] + LISTA_SETORES
        self.combo_setor.addItems(itens_setor)
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
        self.credential_inputs = {}
        self.setWindowTitle(f"Atendimento Solicitação de Acesso #{solicitacao_id}")
        self.setStyleSheet("background-color: #fdfdfd; color: #333333;")
        self.setup_ui()
        self.load_solicitacao()

    def setup_ui(self):
        s = self.controller.buscar_por_id(self.solicitacao_id)
        if s.status == "Em andamento": self.setFixedSize(900, 800)
        elif s.status == "Aberto": self.setFixedSize(900,800)
        else: self.setFixedSize(600, 600)
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
        """
        if s.descricao:
            info_text += f"<br><b>Usuário solicitante:</b><br><div style='background-color:#fff; padding:10px; border-radius:4px; border:1px solid #ddd; color: #333;'>{s.descricao}</div>"

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
        self.credential_inputs.clear()
        
        # Verificar se tem EXPRESSO
        tem_expresso = 'EXPRESSO' in solicitacao.sistemas_solicitados.upper()
        outros_sistemas = [s.strip() for s in solicitacao.sistemas_solicitados.split(',') if s.strip() and s.strip().upper() != 'EXPRESSO']
        
        # Se tiver EXPRESSO, mostrar nota
        if tem_expresso:
            nota = QLabel("<i>Para EXPRESSO, a senha será enviada via email. Preencha as credenciais para os demais sistemas.</i>")
            nota.setStyleSheet("color: #555; font-style: italic; padding: 10px; background-color: #fff9c4; border-radius: 4px;")
            self.action_layout.addWidget(nota)
            self.action_layout.addSpacing(10)
        
        # Se houver outros sistemas além do EXPRESSO, mostrar formulário
        if outros_sistemas:
            self.action_layout.addWidget(QLabel("<b>Preencha as credenciais para cada sistema:</b>"))

            cred_scroll = QScrollArea()
            cred_scroll.setWidgetResizable(True)
            cred_scroll.setStyleSheet("background-color: #C4CFED; border: none;")
            cred_widget = QWidget()
            cred_layout = QVBoxLayout(cred_widget)
            cred_layout.setSpacing(15)

            sistemas = [s.strip() for s in solicitacao.sistemas_solicitados.split(',') if s.strip()]
            
            for sistema in sistemas:
                # Skip EXPRESSO
                if sistema.strip().upper() == 'EXPRESSO':
                    continue
                
                # Frame para cada sistema
                system_frame = QFrame()
                system_frame.setStyleSheet("background-color: white; border: 1px solid #add8e6; border-radius: 4px; padding: 10px;")
                system_layout = QGridLayout(system_frame)
                system_layout.setSpacing(8)
                
                # Título do sistema
                title = QLabel(f"<b>{sistema}</b>")
                system_layout.addWidget(title, 0, 0, 1, 2)
                
                # Login
                lbl_login = QLabel("Login:")
                txt_login = QLineEdit()
                txt_login.setPlaceholderText(f"Login para {sistema}")
                txt_login.setStyleSheet("background-color: #f9f9f9; padding: 5px;")
                system_layout.addWidget(lbl_login, 1, 0)
                system_layout.addWidget(txt_login, 1, 1)
                
                # Senha
                lbl_senha = QLabel("Senha:")
                txt_senha = QLineEdit()
                txt_senha.setPlaceholderText(f"Senha para {sistema}")
                txt_senha.setEchoMode(QLineEdit.Password)
                txt_senha.setStyleSheet("background-color: #f9f9f9; padding: 5px;")
                system_layout.addWidget(lbl_senha, 2, 0)
                system_layout.addWidget(txt_senha, 2, 1)
                
                # Mostrar/Ocultar Senha
                btn_show = QPushButton("Mostrar")
                btn_show.setMaximumWidth(80)
                btn_show.setStyleSheet("padding: 3px; font-size: 10px;")
                
                def toggle_senha(txt_field, btn):
                    if txt_field.echoMode() == QLineEdit.Password:
                        txt_field.setEchoMode(QLineEdit.Normal)
                        btn.setText("Ocultar")
                    else:
                        txt_field.setEchoMode(QLineEdit.Password)
                        btn.setText("Mostrar")
                
                btn_show.clicked.connect(lambda checked=False, tf=txt_senha, btn=btn_show: toggle_senha(tf, btn))
                system_layout.addWidget(btn_show, 2, 2)
                
                cred_layout.addWidget(system_frame)
                self.credential_inputs[sistema] = (txt_login, txt_senha)
            
            cred_layout.addStretch()
            cred_scroll.setWidget(cred_widget)
            self.action_layout.addWidget(cred_scroll)
        else:
            # Se só tiver EXPRESSO
            aviso = QLabel("<b>Aviso:</b> Esta solicitação é apenas para EXPRESSO. Nenhuma credencial adicional precisa ser preenchida aqui.")
            aviso.setStyleSheet("padding: 15px; background-color: #e3f2fd; border: 1px solid #2196F3; border-radius: 4px; color: #1565c0;")
            aviso.setWordWrap(True)
            self.action_layout.addWidget(aviso)

        btn_finish = QPushButton("Finalizar Solicitação"); btn_finish.setObjectName("SubmitBtn")
        btn_finish.clicked.connect(self.finalizar_atendimento)
        self.action_layout.addWidget(btn_finish)

    def build_locked_ui(self, solicitacao):
        lbl = QLabel(f"Esta solicitação já está sendo atendida por <b>{solicitacao.nome_suporte}</b>.")
        self.action_layout.addWidget(lbl)

    def build_readonly_ui(self, solicitacao):
        info = f"<b>Responsável:</b> {solicitacao.nome_suporte}<br><b>Início:</b> {solicitacao.data_inicio_atendimento} | <b>Fim:</b> {solicitacao.data_fechamento}<br><br>"
        lbl = QLabel(info); lbl.setWordWrap(True); lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.action_layout.addWidget(lbl)
        
        # para expresso note
        is_expresso = False
        try:
            if 'EXPRESSO' in solicitacao.sistemas_solicitados.upper():
                is_expresso = True
                note_lbl = QLabel("<i>A senha provisória será enviada para o email fornecido pelo usuário.</i>")
                note_lbl.setStyleSheet("color: #555; font-style: italic;")
                self.action_layout.addWidget(note_lbl)
                self.action_layout.addSpacing(10)
        except Exception:
            pass
        
        # Mostrar credenciais separadas por sistema (filter out expresso later)
        self.action_layout.addWidget(QLabel("<b>Credenciais Criadas:</b>"))
        
        cred_scroll = QScrollArea()
        cred_scroll.setWidgetResizable(True)
        cred_scroll.setStyleSheet("background-color: #C4CFED; border: none;")
        cred_widget = QWidget()
        cred_layout = QVBoxLayout(cred_widget)
        cred_layout.setSpacing(10)
        
        try:
            credenciais_data = json.loads(solicitacao.credenciais_criadas)
            for sistema, cred in credenciais_data.items():
                # skip expresso entry
                if sistema.strip().upper() == 'EXPRESSO':
                    continue
                # Parsear "login|senha"
                if '|' in cred:
                    login, senha = cred.split('|', 1)
                else:
                    login, senha = cred, "***"
                
                # Frame para cada sistema
                system_frame = QFrame()
                system_frame.setStyleSheet("background-color: white; border: 1px solid #add8e6; border-radius: 4px; padding: 10px;")
                system_layout = QVBoxLayout(system_frame)
                system_layout.setSpacing(5)
                
                # Título
                title = QLabel(f"<b>{sistema}</b>")
                system_layout.addWidget(title)
                
                # Login (copiável)
                login_label = QLabel(f"<b>Login:</b> <span style='font-family: monospace; background-color: #f5f5f5; padding: 2px 5px;'>{login}</span>")
                login_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
                system_layout.addWidget(login_label)
                
                # Senha (copiável)
                senha_label = QLabel(f"<b>Senha:</b> <span style='font-family: monospace; background-color: #f5f5f5; padding: 2px 5px;'>{senha}</span>")
                senha_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
                system_layout.addWidget(senha_label)
                
                cred_layout.addWidget(system_frame)
        except (json.JSONDecodeError, TypeError):
            # Se não conseguir parsear JSON, mostrar como texto
            cred_label = QLabel(solicitacao.credenciais_criadas or "N/A")
            cred_label.setWordWrap(True)
            cred_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            cred_layout.addWidget(cred_label)
        
        cred_layout.addStretch()
        cred_scroll.setWidget(cred_widget)
        self.action_layout.addWidget(cred_scroll)

    def iniciar_atendimento(self):
        try: 
            self.controller.assumir_solicitacao(self.solicitacao_id, self.user_suporte.id)
            QMessageBox.information(self, "Sucesso", "Solicitação em execução!")
            self.load_solicitacao()
        except Exception as e: QMessageBox.warning(self, "Erro", str(e))

    def finalizar_atendimento(self):
        try:
            # Montar credenciais a partir dos campos de login e senha separados
            credentials_data = {}
            for sistema, (txt_login, txt_senha) in self.credential_inputs.items():
                login = txt_login.text().strip()
                senha = txt_senha.text().strip()
                
                if not login or not senha:
                    QMessageBox.warning(self, "Atenção", f"Por favor, preencha login e senha para o sistema '{sistema}'.")
                    return
                
                # Salvar no formato "login|senha"
                credentials_data[sistema] = f"{login}|{senha}"
            
            json_data = json.dumps(credentials_data, ensure_ascii=False, indent=4)
            self.controller.finalizar_solicitacao(self.solicitacao_id, self.user_suporte.id, json_data)
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