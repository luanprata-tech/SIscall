# views/user.py
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QLabel, 
    QPushButton, QStackedWidget, QComboBox, QCheckBox, 
    QPlainTextEdit, QTableWidget, QTableWidgetItem, QHeaderView, 
    QAbstractItemView, QMessageBox, QDialog, QScrollArea, QLineEdit
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon, QFont, QColor
from datetime import datetime

# --- USUÁRIO COMUM ---
class UserWindow(QMainWindow): 
    def __init__(self, user, chamado_controller, auth_controller, solicitacao_controller, logout_callback):
        super().__init__()
        self.user = user
        self.controller = chamado_controller
        self.solicitacao_controller = solicitacao_controller
        self.auth_controller = auth_controller
        self.logout_callback = logout_callback
        self.setWindowTitle(f"Painel - {user.nome}")
        
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

        if self.user.tipo == 2:
            self.btn_register = QPushButton("Cadastrar Usuário")
            self.btn_register.setObjectName("MenuBtn")
            self.btn_register.setIcon(QIcon.fromTheme("contact-new"))
            self.btn_register.setCheckable(True)
            self.btn_register.clicked.connect(lambda: self.switch_page(2))
            sidebar_layout.addWidget(self.btn_register)

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

        if self.user.tipo == 2:
            self.page_register = self.create_register_page()
            self.pages.addWidget(self.page_register)

        main_layout.addWidget(sidebar)
        main_layout.addWidget(self.pages)

    def create_open_ticket_page(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignTop)
        
        header = QLabel("Abrir Novo Chamado")
        header.setStyleSheet("font-size: 24px; font-weight: bold; color: #2c3e50; margin: 10px 0;")
        
        form_frame = QWidget()
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
            "COMPUTADOR", "NOTEBOOK", "IMPRESSORA", "TELEFONE",
            "INTERNET", "SCANNER", "CRIAÇÃO DE CONTA", "Outro Dispositivo"
        ])
        self.combo_machine.currentIndexChanged.connect(self.on_machine_changed)
        form_layout.addWidget(self.combo_machine)

        self.contas_container = QWidget()
        self.contas_layout = QVBoxLayout(self.contas_container)
        self.contas_layout.setSpacing(8)
        
        self.contas_label = QLabel("Selecione os sistemas que precisa de conta:")
        self.contas_label.setStyleSheet("color: #2c3e50; font-weight: bold;")
        
        self.checkboxes_contas = {}
        sistemas = ["IGESP","EXPRESSO","REDE","SGI","SISGERI"]
        
        for sistema in sistemas:
            cb = QCheckBox(sistema)
            cb.setStyleSheet("QCheckBox { color: #333; background-color: transparent; }")
            self.checkboxes_contas[sistema] = cb
            self.contas_layout.addWidget(cb)
        
        self.contas_container.setVisible(False)
        form_layout.addWidget(self.contas_label)
        form_layout.addWidget(self.contas_container)

        form_layout.addWidget(QLabel("Descrição do Problema:"))
        self.txt_desc = QPlainTextEdit()
        self.txt_desc.setPlaceholderText("Descreva o motivo do chamado...")
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
        is_conta = self.combo_machine.currentText() == "CRIAÇÃO DE CONTA"
        self.contas_label.setVisible(is_conta)
        self.contas_container.setVisible(is_conta)
        if not is_conta:
            for cb in self.checkboxes_contas.values():
                cb.setChecked(False)

    def create_my_tickets_page(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        header = QLabel("Histórico de Chamados")
        header.setStyleSheet("font-size: 24px; font-weight: bold; color: #2c3e50; margin: 10px 0;")
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setColumnCount(7) 
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
        self.table.verticalHeader().setMinimumSectionSize(70)
        self.table.verticalHeader().setDefaultSectionSize(70)
        self.table.setWordWrap(True)
        
        layout.addWidget(header)
        layout.addWidget(self.table)
        return widget

    def create_register_page(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignTop)
        
        header = QLabel("Cadastrar Novo Usuário")
        header.setStyleSheet("font-size: 24px; font-weight: bold; color: #2c3e50; margin: 10px 0;")
        
        form_frame = QWidget()
        form_frame.setObjectName("TicketFormFrame")
        form_frame.setStyleSheet("""
            #TicketFormFrame { background-color: white; border-radius: 6px; border: 1px solid #ddd; }
            QLabel { color: #333333; background-color: transparent; border: none; }
        """)
        
        form_layout = QVBoxLayout(form_frame)
        form_layout.setSpacing(15)

        self.reg_nome = QLineEdit(); self.reg_nome.setPlaceholderText("Nome")
        form_layout.addWidget(QLabel("Nome:")); form_layout.addWidget(self.reg_nome)

        self.reg_sobrenome = QLineEdit(); self.reg_sobrenome.setPlaceholderText("Sobrenome")
        form_layout.addWidget(QLabel("Sobrenome:")); form_layout.addWidget(self.reg_sobrenome)

        self.reg_login = QLineEdit(); self.reg_login.setPlaceholderText("Login")
        form_layout.addWidget(QLabel("Login:")); form_layout.addWidget(self.reg_login)

        self.reg_senha = QLineEdit(); self.reg_senha.setPlaceholderText("Senha"); self.reg_senha.setEchoMode(QLineEdit.Password)
        form_layout.addWidget(QLabel("Senha:")); form_layout.addWidget(self.reg_senha)

        form_layout.addWidget(QLabel("Setor (Fixo):"))
        self.reg_setor = QLineEdit(self.user.setor)
        self.reg_setor.setReadOnly(True)
        self.reg_setor.setStyleSheet("background-color: #f0f0f0; color: #555;")
        form_layout.addWidget(self.reg_setor)

        btn_submit = QPushButton("Cadastrar Usuário")
        btn_submit.setMinimumHeight(45)
        btn_submit.setObjectName("SubmitBtn")
        btn_submit.clicked.connect(self.registrar_usuario)
        form_layout.addWidget(btn_submit)

        layout.addWidget(header)
        layout.addWidget(form_frame)
        layout.addStretch()
        return widget

    def switch_page(self, index):
        self.pages.setCurrentIndex(index)
        self.btn_new_ticket.setChecked(index == 0)
        self.btn_my_tickets.setChecked(index == 1)
        
        if hasattr(self, 'btn_register'):
            self.btn_register.setChecked(index == 2)
            
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
            
            if c.status == "Aberto": status_item.setForeground(QColor("#d32f2f"))
            elif c.status == "Finalizado": status_item.setForeground(QColor("#2E7D32"))
            else: status_item.setForeground(QColor("#F57C00"))
            table.setItem(i, 5, status_item)
            
            if not is_admin:
                if c.status == "Aberto":
                    btn_del = QPushButton("Excluir"); btn_del.setObjectName("Danger")
                    btn_del.setFixedSize(80, 30)
                    btn_del.clicked.connect(lambda _, cid=c.id: self.deletar_chamado(cid))
                    cell = QWidget(); l = QHBoxLayout(cell); l.setContentsMargins(5,5,5,5); l.addWidget(btn_del); table.setCellWidget(i, 6, cell)
                elif c.status == "Finalizado":
                    btn_details = QPushButton("Detalhes")
                    btn_details.setObjectName("Info")
                    btn_details.setFixedSize(80, 30)
                    btn_details.clicked.connect(lambda _, cid=c.id: self.ver_detalhes_chamado(cid))
                    cell = QWidget(); l = QHBoxLayout(cell); l.setContentsMargins(5,5,5,5); l.addWidget(btn_details); table.setCellWidget(i, 6, cell)
                else: table.setCellWidget(i, 6, QWidget())

    def criar_chamado(self):
        try:
            maquina = self.combo_machine.currentText()
            descricao = self.txt_desc.toPlainText()
            
            if maquina == "CRIAÇÃO DE CONTA":
                contas_selecionadas = [sistema for sistema, cb in self.checkboxes_contas.items() if cb.isChecked()]
                if not contas_selecionadas:
                    raise ValueError("Selecione pelo menos um sistema para criação de conta!")
                self.solicitacao_controller.criar_solicitacao(self.user.id, descricao, contas_selecionadas)
                QMessageBox.information(self, "Sucesso", "Solicitação de conta registrada!")
            else:
                self.controller.criar_chamado(self.user.id, descricao, maquina)            
                QMessageBox.information(self, "Sucesso", "Chamado registrado!")

            self.txt_desc.clear()
            self.combo_machine.setCurrentIndex(0)
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

    def ver_detalhes_chamado(self, chamado_id):
        try:
            chamado = self.controller.buscar_por_id(chamado_id)
            if not chamado:
                QMessageBox.warning(self, "Erro", "Chamado não encontrado!")
                return
            
            dialog = QDialog(self)
            dialog.setWindowTitle(f"Detalhes do Chamado #{chamado_id}")
            dialog.setFixedSize(500, 400)
            dialog.setStyleSheet("background-color: #f0f3f4;")
            
            layout = QVBoxLayout(dialog)
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setStyleSheet("border: none;")
            scroll_content = QWidget()
            scroll_content.setStyleSheet("background-color: #f0f3f4;")
            scroll_layout = QVBoxLayout(scroll_content)
            
            lbl_desc_title = QLabel("<b>Problema:</b>")
            scroll_layout.addWidget(lbl_desc_title)
            lbl_desc = QLabel(chamado.descricao)
            lbl_desc.setWordWrap(True)
            lbl_desc.setStyleSheet("background-color:#f5f5f5; padding:10px; border-radius:4px;")
            scroll_layout.addWidget(lbl_desc)
            
            if chamado.diagnostico:
                scroll_layout.addWidget(QLabel("<b>Diagnóstico:</b>"))
                lbl_diag = QLabel(chamado.diagnostico)
                lbl_diag.setWordWrap(True)
                scroll_layout.addWidget(lbl_diag)
            
            if chamado.solucao:
                scroll_layout.addWidget(QLabel("<b>Solução:</b>"))
                lbl_sol = QLabel(chamado.solucao)
                lbl_sol.setWordWrap(True)
                scroll_layout.addWidget(lbl_sol)
            
            scroll_layout.addStretch()
            scroll.setWidget(scroll_content)
            layout.addWidget(scroll)
            
            btn_close = QPushButton("Fechar")
            btn_close.clicked.connect(dialog.accept)
            layout.addWidget(btn_close)
            
            dialog.exec()
        except Exception as e:
            QMessageBox.warning(self, "Erro", f"Erro ao abrir detalhes: {str(e)}")

    def registrar_usuario(self):
        try:
            self.auth_controller.cadastrar_usuario(
                self.reg_nome.text(), self.reg_sobrenome.text(),
                self.reg_login.text(), self.reg_senha.text(),
                self.user.setor
            )
            QMessageBox.information(self, "Sucesso", "Usuário cadastrado com sucesso!")
            self.reg_nome.clear(); self.reg_sobrenome.clear(); self.reg_login.clear(); self.reg_senha.clear()
        except Exception as e:
            QMessageBox.warning(self, "Erro", str(e))