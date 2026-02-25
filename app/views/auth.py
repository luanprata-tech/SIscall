# views/auth.py
from PySide6.QtWidgets import (
    QDialog, QMainWindow, QVBoxLayout, QLabel, QLineEdit, 
    QPushButton, QMessageBox, QComboBox, QWidget
)
from PySide6.QtCore import Qt
from .common import CenterMixin

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
        layout.addWidget(title); layout.addWidget(self.txt_user); layout.addWidget(self.txt_pass); layout.addWidget(btn_login)
        
    def perform_login(self):
        if self.logging_in: return
        self.logging_in = True
        try:
            user = self.auth.login(self.txt_user.text(), self.txt_pass.text())
            if user:
                if user.trocar_senha: 
                    ChangePasswordDialog(self.auth, user.id, lambda: self.on_success(user)).exec()
                    self.close()
                else: 
                    self.on_success(user)
            else: 
                QMessageBox.warning(self, "Erro", "Login inválido.")
                self.logging_in = False
        except Exception as e: 
            self.logging_in = False
            QMessageBox.critical(self, "Erro", str(e))
            