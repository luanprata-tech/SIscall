# views/dialogs.py
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QComboBox, QPushButton, QFileDialog,
    QLineEdit, QMessageBox, QScrollArea, QWidget, QFrame, QPlainTextEdit,
    QGridLayout, QHBoxLayout
)
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices, QPixmap
from .common import CenterMixin, LISTA_SETORES
import json
import os

# --- DIALOG PARA VER IMAGEM EM TELA CHEIA ---
class ImageViewDialog(QDialog, CenterMixin):
    def __init__(self, image_data, filename=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Visualizar Imagem")
        self.setStyleSheet("background-color: #fdfdfd;")
        self.setup_ui(image_data, filename)

    def setup_ui(self, image_data, filename):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Carrega a imagem
        pixmap = QPixmap()
        pixmap.loadFromData(image_data)
        
        # Calcula tamanho para manter proporção e não exceder 800x600
        img_width = pixmap.width()
        img_height = pixmap.height()
        max_width, max_height = 1000, 700
        
        if img_width > max_width or img_height > max_height:
            pixmap = pixmap.scaledToWidth(max_width, Qt.SmoothTransformation) if img_width > max_width else pixmap
            if pixmap.height() > max_height:
                pixmap = pixmap.scaledToHeight(max_height, Qt.SmoothTransformation)
        
        # Exibe a imagem
        lbl_img = QLabel()
        lbl_img.setPixmap(pixmap)
        lbl_img.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_img)
        
        # Botões
        btn_layout = QHBoxLayout()
        
        btn_save = QPushButton("Salvar Imagem...")
        btn_save.setObjectName("Info")
        btn_save.setStyleSheet("background-color: #2196F3; color: white; padding: 8px; border-radius: 4px; font-weight: bold;")
        def save_image():
            filePath, _ = QFileDialog.getSaveFileName(self, "Salvar Imagem Como...", filename or "imagem.png", "Imagens (*.png *.jpg *.jpeg)")
            if filePath:
                try:
                    with open(filePath, 'wb') as f:
                        f.write(image_data)
                    QMessageBox.information(self, "Sucesso", "Imagem salva com sucesso!")
                except Exception as e:
                    QMessageBox.warning(self, "Erro", f"Não foi possível salvar a imagem: {e}")
        btn_save.clicked.connect(save_image)
        btn_layout.addWidget(btn_save)
        
        btn_close = QPushButton("Fechar")
        btn_close.setObjectName("Info")
        btn_close.setStyleSheet("background-color: #607D8B; color: white; padding: 8px; border-radius: 4px; font-weight: bold;")
        btn_close.clicked.connect(self.close)
        btn_layout.addWidget(btn_close)
        
        layout.addLayout(btn_layout)
        
        self.setFixedSize(1050, 750)

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
        self.reopen_requested = False
        self.setWindowTitle(f"Atendimento Solicitação de Acesso #{solicitacao_id}")
        self.setStyleSheet("background-color: #fdfdfd; color: #333333;")
        self.setup_ui()
        self.load_solicitacao()

    def setup_ui(self):
        s = self.controller.buscar_por_id(self.solicitacao_id)
        if s.status == "Em andamento" or s.status == "Em espera": self.setFixedSize(950, 760)
        elif s.status == "Aberto": self.setFixedSize(820, 700)
        else: self.setFixedSize(560, 520)
        self.layout = QVBoxLayout(self)
        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setStyleSheet("background-color: #fdfdfd; border: none;") 
        scroll_content = QWidget(); scroll_content.setStyleSheet("background-color: #fdfdfd;")
        self.details_layout = QVBoxLayout(scroll_content)
        self.lbl_info = QLabel()
        self.lbl_info.setStyleSheet("font-size: 15px; line-height: 1.5; color: #333;")
        self.lbl_info.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.lbl_info.setWordWrap(True)
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
        <b>Status:</b> <b style='font-size:16px; color:{'red' if s.status=='Aberto' else 'blue' if s.status=='Resolvido' else 'gray' if s.status=='Em espera' else 'green' if s.status=='Finalizado' else 'orange'}'>{s.status.upper()}</b><br>        
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
        elif s.status == "Em espera":
            if s.suporte_id == self.user_suporte.id: self.build_wait_ui_solicitacao(s)
            else: self.build_locked_ui(s)
        else: self.build_readonly_ui(s)

    def build_start_ui(self):
        lbl = QLabel("Esta solicitação está aguardando atendimento.")
        btn_start = QPushButton("Iniciar Atendimento"); btn_start.setObjectName("SubmitBtn")
        btn_start.clicked.connect(self.iniciar_atendimento)
        self.action_layout.addWidget(lbl); self.action_layout.addWidget(btn_start)

    def _adicionar_editor_resposta(self):
        self.txt_resposta = QPlainTextEdit()
        self.txt_resposta.setPlaceholderText("Escreva aqui a resposta ao usuário...")
        self.txt_resposta.setStyleSheet("background-color: white; color: #333;")
        self.txt_resposta.setFixedHeight(150)
        self.action_layout.addWidget(self.txt_resposta)

    def _formatar_resposta_atendimento(self, resposta):
        if not resposta:
            return "N/A"

        try:
            dados = json.loads(resposta)
        except (json.JSONDecodeError, TypeError):
            return resposta

        if isinstance(dados, dict):
            linhas = []
            for sistema, valor in dados.items():
                if isinstance(valor, str):
                    valor = valor.replace("|", " / ")
                linhas.append(f"{sistema}: {valor}")
            return "\n".join(linhas) if linhas else "N/A"

        return resposta

    def build_finish_ui(self, solicitacao):
        # Botão para colocar em espera
        btn_wait = QPushButton("Colocar em Espera")
        btn_wait.setObjectName("WarningBtn")
        btn_wait.clicked.connect(self.marcar_solicitacao_em_espera)
        self.action_layout.addWidget(btn_wait)
        self.action_layout.addSpacing(15)
        
        self.action_layout.addWidget(QLabel("<b>Ou finalize o atendimento:</b>"))

        self._adicionar_editor_resposta()

        btn_finish = QPushButton("Finalizar Solicitação"); btn_finish.setObjectName("SubmitBtn")
        btn_finish.clicked.connect(self.finalizar_atendimento)
        self.action_layout.addWidget(btn_finish)

    def build_wait_ui_solicitacao(self, solicitacao):
        btn_continue = QPushButton("Continuar Atendimento")
        btn_continue.setObjectName("SubmitBtn")
        btn_continue.clicked.connect(self.continuar_solicitacao_de_espera)
        
        self.action_layout.addWidget(btn_continue)
        
        self.action_layout.addWidget(QLabel("<b>Ou finalize o atendimento:</b>"))

        self._adicionar_editor_resposta()

        btn_finish = QPushButton("Finalizar Solicitação"); btn_finish.setObjectName("SubmitBtn")
        btn_finish.clicked.connect(self.finalizar_de_espera_solicitacao)
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

        resposta = self._formatar_resposta_atendimento(solicitacao.credenciais_criadas)
        self.action_layout.addWidget(QLabel("<b>Resposta do atendimento:</b>"))
        resposta_label = QLabel(resposta)
        resposta_label.setWordWrap(True)
        resposta_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        resposta_label.setStyleSheet("background-color: #fff3cd; padding: 10px; border-radius: 4px; border: 1px solid #ffc107;")
        self.action_layout.addWidget(resposta_label)

    def iniciar_atendimento(self):
        try: 
            self.controller.assumir_solicitacao(self.solicitacao_id, self.user_suporte.id)
            QMessageBox.information(self, "Sucesso", "Solicitação em execução!")
            self.solicitar_reabertura()
        except Exception as e: QMessageBox.warning(self, "Erro", str(e))

    def marcar_solicitacao_em_espera(self):
        try:
            self.controller.marcar_em_espera(self.solicitacao_id, self.user_suporte.id)
            QMessageBox.information(self, "Sucesso", "Solicitação marcada como em espera!")
            self.load_solicitacao()
        except Exception as e:
            QMessageBox.warning(self, "Erro", str(e))

    def continuar_solicitacao_de_espera(self):
        try:
            self.controller.continuar_de_espera(self.solicitacao_id, self.user_suporte.id)
            QMessageBox.information(self, "Sucesso", "Solicitação retomada! Status agora é em andamento.")
            self.load_solicitacao()
        except Exception as e:
            QMessageBox.warning(self, "Erro", str(e))

    def finalizar_de_espera_solicitacao(self):
        try:
            resposta = self.txt_resposta.toPlainText().strip()
            self.controller.resolver_de_espera(self.solicitacao_id, self.user_suporte.id, resposta)
            QMessageBox.information(self, "Sucesso", "Solicitação finalizada!")
            self.accept()
        except Exception as e:
            QMessageBox.warning(self, "Erro", str(e))

    def finalizar_atendimento(self):
        try:
            resposta = self.txt_resposta.toPlainText().strip()
            self.controller.finalizar_solicitacao(self.solicitacao_id, self.user_suporte.id, resposta)
            QMessageBox.information(self, "Sucesso", "Solicitação finalizada!")
            self.accept()
        except Exception as e:
            QMessageBox.warning(self, "Erro", str(e))

    def solicitar_reabertura(self):
        self.reopen_requested = True
        self.accept()

# --- JANELA DE AÇÃO DO SUPORTE ---
class TicketActionDialog(QDialog, CenterMixin):
    def __init__(self, chamado_id, controller, user_suporte, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.chamado_id = chamado_id
        self.user_suporte = user_suporte
        self.reopen_requested = False
        self.setWindowTitle(f"Atendimento Chamado #{chamado_id}")
        self.setStyleSheet("background-color: #fdfdfd; color: #333333;")
        self.setup_ui()
        self.load_chamado()

    def setup_ui(self):
        c = self.controller.buscar_por_id(self.chamado_id)
        if c.status == "Em andamento" or c.status == "Em espera": self.setFixedSize(1020, 800)
        elif c.status == "Aberto": self.setFixedSize(600,500)
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
        self.lbl_info.setWordWrap(True)
        self.details_layout.addWidget(self.lbl_info)        

        # Container para a imagem, para que possamos limpá-lo e recriá-lo
        self.image_container = QWidget()
        self.image_layout = QVBoxLayout(self.image_container)
        self.image_layout.setContentsMargins(0, 0, 0, 0)
        self.details_layout.addWidget(self.image_container)

        self.details_layout.addStretch()

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
        <b>Status:</b> <b style='font-size:16px; color:{'red' if c.status=='Aberto' else 'blue' if c.status=='Resolvido' else 'gray' if c.status=='Em espera' else 'green' if c.status=='Finalizado' else 'orange'}'>{c.status.upper()}</b><br>
        <hr>
        <b>Descrição:</b><br>
        <div style='background-color:#fff; padding:10px; border-radius:4px; border:1px solid #ddd; color: #333;'>{c.descricao}</div>
        """
        
        self.lbl_info.setText(info_text)

        # Limpa o container da imagem anterior
        while self.image_layout.count():
            child = self.image_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # Adiciona botão para ver imagem se existir
        if c.imagem_data:
            btn_view_img = QPushButton("🖼️ Ver Imagem Anexada")
            btn_view_img.setObjectName("Info")
            btn_view_img.setStyleSheet("background-color: #2196F3; color: white; padding: 8px; border-radius: 4px; font-weight: bold;")
            btn_view_img.clicked.connect(lambda: ImageViewDialog(c.imagem_data, getattr(c, 'imagem_filename', 'imagem.png'), self).exec())
            self.image_layout.addWidget(btn_view_img)

        while self.action_layout.count():
            child = self.action_layout.takeAt(0)
            if child.widget(): child.widget().deleteLater()
        if c.status == "Aberto": self.build_start_ui()
        elif c.status == "Em andamento":
            if c.suporte_id == self.user_suporte.id: self.build_finish_ui(c)
            else: self.build_locked_ui(c)
        elif c.status == "Em espera":
            if c.suporte_id == self.user_suporte.id: self.build_wait_ui(c)
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
        self.action_layout.addWidget(lbl)

        self.action_layout.addWidget(QLabel("Motivo da espera (opcional):"))
        self.txt_motivo_espera = QLineEdit()
        self.txt_motivo_espera.setPlaceholderText("Ex.: aguardando retorno do usuário / fornecedor")
        self.txt_motivo_espera.setStyleSheet("background-color: white; color: #333;")
        self.action_layout.addWidget(self.txt_motivo_espera)
        
        # Botão para colocar em espera
        btn_wait = QPushButton("Colocar em Espera")
        btn_wait.setObjectName("WarningBtn")
        btn_wait.clicked.connect(self.marcar_em_espera)
        self.action_layout.addWidget(btn_wait)
        
        self.action_layout.addWidget(QLabel("<b>Ou finalize o atendimento:</b>"))
        
        btn_finish = QPushButton("Marcar como Resolvido")
        btn_finish.setObjectName("SubmitBtn")
        btn_finish.clicked.connect(self.resolver_atendimento)
        
        self.txt_diag = QPlainTextEdit()
        self.txt_diag.setPlaceholderText("Diagnóstico técnico...")
        self.txt_diag.setStyleSheet("background-color: white; color: #333;")
        self.txt_diag.setFixedHeight(80)
        self.txt_solucao = QPlainTextEdit()
        self.txt_solucao.setPlaceholderText("Solução aplicada...")
        self.txt_solucao.setStyleSheet("background-color: white; color: #333;")
        self.txt_solucao.setFixedHeight(80)
        self.action_layout.addWidget(QLabel("Diagnóstico:"))
        self.action_layout.addWidget(self.txt_diag)
        self.action_layout.addWidget(QLabel("Solução:"))
        self.action_layout.addWidget(self.txt_solucao)
        
        self.action_layout.addWidget(btn_finish)

    def build_wait_ui(self, chamado):
        btn_continue = QPushButton("Continuar Atendimento")
        btn_continue.setObjectName("SubmitBtn")
        btn_continue.clicked.connect(self.continuar_de_espera)
        
        self.action_layout.addWidget(btn_continue)
        
        self.action_layout.addWidget(QLabel("<b>Ou finalize o atendimento:</b>"))
        
        btn_finish = QPushButton("Marcar como Resolvido")
        btn_finish.setObjectName("SubmitBtn")
        btn_finish.clicked.connect(self.resolver_de_espera)
        
        self.txt_diag = QPlainTextEdit()
        self.txt_diag.setPlaceholderText("Diagnóstico técnico...")
        self.txt_diag.setStyleSheet("background-color: white; color: #333;")
        self.txt_diag.setFixedHeight(80)
        self.txt_solucao = QPlainTextEdit()
        self.txt_solucao.setPlaceholderText("Solução aplicada...")
        self.txt_solucao.setStyleSheet("background-color: white; color: #333;")
        self.txt_solucao.setFixedHeight(80)
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

        if hasattr(chamado, 'observacao_confirmacao') and chamado.observacao_confirmacao:
            self.action_layout.addWidget(QLabel("<b>Observação da confirmação:</b>"))
            lbl_obs = QLabel(chamado.observacao_confirmacao)
            lbl_obs.setWordWrap(True)
            lbl_obs.setTextInteractionFlags(Qt.TextSelectableByMouse)
            lbl_obs.setStyleSheet("background-color:#eef6ff; padding:10px; border-radius:4px; border:1px solid #cfe3ff;")
            self.action_layout.addWidget(lbl_obs)

    def iniciar_atendimento(self):
        try: 
            self.controller.assumir_chamado(self.chamado_id, self.user_suporte.id)
            QMessageBox.information(self, "Sucesso", "Chamado em execução!")
            self.reopen_requested = True
            self.accept()
        except Exception as e: QMessageBox.warning(self, "Erro", str(e))

    def marcar_em_espera(self):
        try:
            motivo_espera = ""
            if hasattr(self, 'txt_motivo_espera'):
                motivo_espera = self.txt_motivo_espera.text().strip()

            self.controller.marcar_em_espera(self.chamado_id, self.user_suporte.id, motivo_espera)
            QMessageBox.information(self, "Sucesso", "Chamado marcado como em espera!")
            self.load_chamado()
        except Exception as e:
            QMessageBox.warning(self, "Erro", str(e))

    def continuar_de_espera(self):
        try:
            self.controller.continuar_de_espera(self.chamado_id, self.user_suporte.id)
            QMessageBox.information(self, "Sucesso", "Chamado retomado! Status agora é em andamento.")
            self.load_chamado()
        except Exception as e:
            QMessageBox.warning(self, "Erro", str(e))

    def resolver_de_espera(self):
        try:
            self.controller.resolver_de_espera(self.chamado_id, self.user_suporte.id, self.txt_diag.toPlainText(), self.txt_solucao.toPlainText())
            QMessageBox.information(self, "Sucesso", "Chamado marcado como resolvido! Aguardando confirmação do usuário.")
            self.accept()
        except Exception as e:
            QMessageBox.warning(self, "Erro", str(e))

    def resolver_atendimento(self):
        try:
            self.controller.resolver_chamado(self.chamado_id, self.user_suporte.id, self.txt_diag.toPlainText(), self.txt_solucao.toPlainText())
            QMessageBox.information(self, "Sucesso", "Chamado marcado como resolvido! Aguardando confirmação do usuário.")
            self.accept()
        except Exception as e:
            QMessageBox.warning(self, "Erro", str(e))