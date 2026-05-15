# views/admin.py
import os
import sys
import socket
import getpass
import platform
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QLabel, 
    QPushButton, QStackedWidget, QTableWidget, QTableWidgetItem, 
    QHeaderView, QAbstractItemView, QMessageBox, QDialog, QScrollArea, QFileDialog,
    QFrame, QDateEdit, QGroupBox, QGridLayout, QCheckBox,
    QLineEdit, QComboBox
)
from PySide6.QtCore import Qt, QTimer, QDate
from PySide6.QtGui import QIcon, QFont, QColor, QPixmap, QDesktopServices
from datetime import datetime, timedelta
from .common import LISTA_SETORES, apply_table_shadow
from .dialogs import TicketActionDialog, UserEditDialog, UserRegisterDialog, AccountRequestActionDialog
from . import reports

# --- ADMIN WINDOW (MAXIMIZADO + RELATÓRIOS + GESTÃO) ---
class AdminWindow(QMainWindow): 
    def __init__(self, user, chamado_controller, auth_controller, solicitacao_controller, ip_controller, logout_callback):
        super().__init__()
        self.user = user
        self.controller = chamado_controller
        self.auth_controller = auth_controller
        self.solicitacao_controller = solicitacao_controller
        self.ip_controller = ip_controller
        self.logout_callback = logout_callback
        # Definir ícone da janela (usa assets/icon.ico e suporta PyInstaller)
        try:
            def resource_path(relative_path: str) -> str:
                if getattr(sys, 'frozen', False):
                    base_path = getattr(sys, '_MEIPASS', os.path.abspath('.'))
                else:
                    base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
                return os.path.join(base_path, 'assets', relative_path)

            icon_path = resource_path('icon.ico')
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
        except Exception:
            pass
        self.setWindowTitle(f"Painel Admin - {user.nome}")

        self.items_per_page = 20
        self.current_page_historico = 1
        self.total_pages_historico = 1
        self.ip_statuses = ["Livre", "Alocado", "Reservado", "Bloqueado"]

        self.setup_ui()
        QTimer.singleShot(100, self.showMaximized) 
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_data)
        self.timer.start(1000) 
        self.refresh_data()

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

        self.btn_reports = QPushButton("Relatórios"); self.btn_reports.setObjectName("MenuBtn"); self.btn_reports.setCheckable(True); self.btn_reports.clicked.connect(lambda: self.switch_page(3))
        self.btn_ips = QPushButton("Gestão de IPs"); self.btn_ips.setObjectName("MenuBtn"); self.btn_ips.setCheckable(True); self.btn_ips.clicked.connect(lambda: self.switch_page(4))
        self.btn_config = QPushButton("Configurações"); self.btn_config.setObjectName("MenuBtn"); self.btn_config.setIcon(QIcon.fromTheme("preferences-system")); self.btn_config.setCheckable(True); self.btn_config.clicked.connect(lambda: self.switch_page(5))
        btn_logout = QPushButton("Sair"); btn_logout.setObjectName("MenuBtn"); btn_logout.setStyleSheet("color: #ff6b6b;"); btn_logout.clicked.connect(self.logout_callback)

        sidebar_layout.addWidget(lbl_brand); sidebar_layout.addSpacing(20); sidebar_layout.addWidget(self.btn_work); sidebar_layout.addWidget(self.btn_all)

        # Botão de Solicitações de Conta com badge
        self.btn_accounts = QPushButton()
        self.btn_accounts.setObjectName("MenuBtn")
        self.btn_accounts.setCheckable(True)
        self.btn_accounts.clicked.connect(lambda: self.switch_page(2))
        btn_layout = QHBoxLayout(self.btn_accounts)
        btn_layout.setContentsMargins(20, 12, 20, 12)
        btn_layout.setSpacing(5)
        text_label = QLabel("Solicitações de Acesso")
        self.lbl_accounts_count = QLabel("0")
        self.lbl_accounts_count.setObjectName("CountBadge")
        self.lbl_accounts_count.setAlignment(Qt.AlignCenter)
        self.lbl_accounts_count.setVisible(False)
        btn_layout.addWidget(text_label)
        btn_layout.addStretch()
        btn_layout.addWidget(self.lbl_accounts_count)
        sidebar_layout.addWidget(self.btn_accounts)

        sidebar_layout.addWidget(self.btn_reports); sidebar_layout.addWidget(self.btn_ips); sidebar_layout.addWidget(self.btn_config); sidebar_layout.addStretch(); sidebar_layout.addWidget(btn_logout)

        self.pages = QStackedWidget()
        self.page_work = self.create_table_page("Chamados Pendentes", edit_mode=True)
        self.page_all = self.create_table_page("Histórico Completo", edit_mode=False)
        self.page_accounts = self.create_accounts_table_page()
        self.page_reports = self.create_reports_page() # Será o índice 3 agora
        self.page_ips = self.create_ips_page()
        self.page_config_widget = self.create_config_page()

        self.pages.addWidget(self.page_work['widget'])
        self.pages.addWidget(self.page_all['widget'])
        self.pages.addWidget(self.page_accounts['widget'])
        self.pages.addWidget(self.page_reports)
        self.pages.addWidget(self.page_ips)
        self.pages.addWidget(self.page_config_widget)

        main_layout.addWidget(sidebar)
        main_layout.addWidget(self.pages)

        # Conectar sinais da paginação
        if 'btn_prev' in self.page_all:
            self.page_all['btn_prev'].clicked.connect(self.prev_page_historico)
            self.page_all['btn_next'].clicked.connect(self.next_page_historico)

    def create_table_page(self, title_text, edit_mode):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        header = QLabel(title_text)
        header.setStyleSheet("font-size: 24px; font-weight: bold; color: #2c3e50; margin: 15px 5px;")
        table = QTableWidget()
        table.setAlternatingRowColors(True)
        cols = ["Setor", "Usuário", "Máquina", "Hora", "Data", "Descrição", "Status", "Ação"]
        if not edit_mode:
            cols = ["Setor", "Usuário", "Máquina", "Hora", "Data", "Descrição", "Status", "Ação"]
        table.setColumnCount(len(cols))
        table.setHorizontalHeaderLabels(cols)

        table.setColumnWidth(0, 150)
        table.setColumnWidth(1, 150)
        table.setColumnWidth(2, 150)
        table.setColumnWidth(3, 90)
        table.setColumnWidth(4, 90)
        table.setColumnWidth(6, 150)
        table.setColumnWidth(7, 220)
        table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch)

        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.verticalHeader().setVisible(False)
        table.verticalHeader().setMinimumSectionSize(70)
        table.verticalHeader().setDefaultSectionSize(70)
        table.setWordWrap(True)
        apply_table_shadow(table)
        layout.addWidget(header)
        layout.addWidget(table)

        page_elements = {'widget': widget, 'table': table, 'edit_mode': edit_mode}

        if not edit_mode:
            pagination_widget = QWidget()
            pagination_layout = QHBoxLayout(pagination_widget)
            btn_prev = QPushButton("<< Anterior")
            lbl_page = QLabel("Página 1 / 1")
            lbl_page.setAlignment(Qt.AlignCenter)
            btn_next = QPushButton("Próximo >>")

            pagination_layout.addStretch()
            pagination_layout.addWidget(btn_prev)
            pagination_layout.addWidget(lbl_page)
            pagination_layout.addWidget(btn_next)
            pagination_layout.addStretch()

            layout.addWidget(pagination_widget)

            page_elements.update({'btn_prev': btn_prev, 'btn_next': btn_next, 'lbl_page': lbl_page})

        return page_elements

    def create_accounts_table_page(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        header = QLabel("Solicitações de Acesso Pendentes")
        header.setStyleSheet("font-size: 24px; font-weight: bold; color: #2c3e50; margin: 15px 5px;")

        table = QTableWidget()
        table.setAlternatingRowColors(True)
        cols = ["Setor", "Usuário", "Sistemas Solicitados", "Hora", "Data", "Status", "Ação"]
        table.setColumnCount(len(cols))
        table.setHorizontalHeaderLabels(cols)

        table.setColumnWidth(0, 150)
        table.setColumnWidth(1, 150)
        table.setColumnWidth(3, 90)
        table.setColumnWidth(4, 90)
        table.setColumnWidth(5, 150)
        table.setColumnWidth(6, 220)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)

        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.verticalHeader().setVisible(False)
        table.verticalHeader().setMinimumSectionSize(70)
        table.verticalHeader().setDefaultSectionSize(70)
        table.setWordWrap(True)

        layout.addWidget(header)
        layout.addWidget(table)
        return {'widget': widget, 'table': table}

    # --- RELATÓRIOS ---
    def create_reports_page(self):
        return reports.ReportsPage(self, self.controller)

    def create_ips_page(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        header = QLabel("Gestão de IPs")
        header.setStyleSheet("font-size: 24px; font-weight: bold; color: #2c3e50; margin: 15px 5px;")
        layout.addWidget(header)
        filter_layout = QHBoxLayout()
        self.txt_search_ip = QLineEdit()
        self.txt_search_ip.setPlaceholderText("Buscar por IP, máquina, usuário, setor ou status...")
        self.txt_search_ip.textChanged.connect(self.load_ips)

        self.combo_filter_ip_status = QComboBox()
        self.combo_filter_ip_status.addItems(["Todos"] + self.ip_statuses)
        self.combo_filter_ip_status.currentTextChanged.connect(self.load_ips)

        btn_refresh_ips = QPushButton("Atualizar")
        btn_refresh_ips.clicked.connect(self.load_ips)

        filter_layout.addWidget(self.txt_search_ip, 1)
        filter_layout.addWidget(self.combo_filter_ip_status)
        filter_layout.addWidget(btn_refresh_ips)
        layout.addLayout(filter_layout)

        self.table_ips = QTableWidget()
        self.table_ips.setAlternatingRowColors(True)
        self.table_ips.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_ips.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table_ips.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table_ips.verticalHeader().setVisible(False)
        self.table_ips.verticalHeader().setMinimumSectionSize(65)
        self.table_ips.verticalHeader().setDefaultSectionSize(65)
        self.table_ips.setColumnCount(8)
        self.table_ips.setHorizontalHeaderLabels([
            "IP", "Máquina", "Nome da máquina", "Nome do usuário", "Setor", "Status", "Modificado em", "Ações"
        ])
        self.table_ips.setColumnWidth(0, 160)
        self.table_ips.setColumnWidth(1, 220)
        self.table_ips.setColumnWidth(2, 360)
        self.table_ips.setColumnWidth(3, 360)
        self.table_ips.setColumnWidth(4, 300)
        self.table_ips.setColumnWidth(5, 160)
        self.table_ips.setColumnWidth(6, 180)
        self.table_ips.setColumnWidth(7, 120)
        self.table_ips.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table_ips.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.table_ips.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.table_ips.horizontalHeader().setSectionResizeMode(6, QHeaderView.Fixed)
        self.table_ips.horizontalHeader().setSectionResizeMode(7, QHeaderView.Fixed)
        apply_table_shadow(self.table_ips)
        layout.addWidget(self.table_ips)

        self.load_ips()
        return widget

    # --- CONFIG (GESTÃO DE USUÁRIOS) ---
    def create_config_page(self):
        widget = QWidget(); layout = QVBoxLayout(widget); layout.setAlignment(Qt.AlignTop)
        header = QLabel("Gestão de Usuários")
        header.setStyleSheet("font-size: 24px; font-weight: bold; color: #2c3e50; margin: 15px 5px;")
        layout.addWidget(header)
        filter_layout = QHBoxLayout()
        self.txt_search_user = QLineEdit()
        self.txt_search_user.setPlaceholderText("Buscar por Nome ou Login...")
        self.txt_search_user.textChanged.connect(self.load_users)
        self.combo_filter_setor = QComboBox()
        self.combo_filter_setor.addItems(["Todos"] + LISTA_SETORES)
        self.combo_filter_setor.currentTextChanged.connect(self.load_users)
        
        self.check_incluir_inativos = QCheckBox("Ver inativos")
        self.check_incluir_inativos.stateChanged.connect(self.load_users)

        btn_new_user = QPushButton("Novo Usuário")
        btn_new_user.setIcon(QIcon.fromTheme("contact-new"))
        btn_new_user.clicked.connect(self.abrir_cadastro_usuario)
        
        filter_layout.addWidget(self.txt_search_user, 1)
        filter_layout.addWidget(self.combo_filter_setor)
        filter_layout.addStretch()
        filter_layout.addWidget(self.check_incluir_inativos)
        filter_layout.addWidget(btn_new_user)
        layout.addLayout(filter_layout)
        
        self.table_users = QTableWidget()
        self.table_users.setAlternatingRowColors(True)
        self.table_users.setColumnCount(4)
        self.table_users.setHorizontalHeaderLabels(["Nome", "Login", "Setor", "Ações"])
        
        self.table_users.setColumnWidth(1, 150)
        self.table_users.setColumnWidth(2, 200)
        self.table_users.setColumnWidth(3, 220)
        self.table_users.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        
        self.table_users.verticalHeader().setMinimumSectionSize(70) 
        self.table_users.verticalHeader().setDefaultSectionSize(70) 
        self.table_users.verticalHeader().setVisible(False)
        self.table_users.setEditTriggers(QAbstractItemView.NoEditTriggers)
        apply_table_shadow(self.table_users)
        layout.addWidget(self.table_users)
        return widget

    def switch_page(self, index):
        self.pages.setCurrentIndex(index)
        self.btn_work.setChecked(index == 0)
        self.btn_all.setChecked(index == 1)
        self.btn_accounts.setChecked(index == 2)
        self.btn_reports.setChecked(index == 3)
        self.btn_ips.setChecked(index == 4)
        self.btn_config.setChecked(index == 5)

        if index == 1: self.current_page_historico = 1

        if index == 5: self.load_users()
        elif index == 3: pass # Relatórios
        elif index == 4: self.load_ips()
        elif index == 2: self.refresh_data()
        else: self.refresh_data()

    def load_ips(self):
        if not hasattr(self, 'ip_controller') or not self.ip_controller:
            return

        termo = self.txt_search_ip.text().strip() if hasattr(self, 'txt_search_ip') else ""
        status = self.combo_filter_ip_status.currentText() if hasattr(self, 'combo_filter_ip_status') else "Todos"
        ips = self.ip_controller.listar_ips(termo, status)

        self.table_ips.setRowCount(len(ips))
        for i, registro in enumerate(ips):
            self.table_ips.setItem(i, 0, QTableWidgetItem(registro.ip_address))
            self.table_ips.setItem(i, 1, QTableWidgetItem(registro.maquina or "-"))
            self.table_ips.setItem(i, 2, QTableWidgetItem(registro.nome_maquina or "-"))
            self.table_ips.setItem(i, 3, QTableWidgetItem(registro.nome_usuario or "-"))
            self.table_ips.setItem(i, 4, QTableWidgetItem(registro.setor or "-"))

            status_item = QTableWidgetItem(registro.status or "Livre")
            status_item.setTextAlignment(Qt.AlignCenter)
            self.table_ips.setItem(i, 5, status_item)

            self.table_ips.setItem(i, 6, QTableWidgetItem(registro.data_modificacao or "-"))

            btn_editar = QPushButton("Editar")
            btn_editar.setFixedSize(78, 35)
            btn_editar.clicked.connect(lambda _, ip=registro.ip_address: self.abrir_form_ip(ip))

            container = QWidget()
            row_layout = QHBoxLayout(container)
            row_layout.setContentsMargins(6, 2, 6, 2)
            row_layout.setSpacing(6)
            row_layout.addWidget(btn_editar)
            self.table_ips.setCellWidget(i, 7, container)

        if ips:
            self.table_ips.selectRow(0)

    def obter_informacoes_maquina(self):
        """
        Coleta as informações da máquina local:
        - IP local (apenas se estiver no prefixo 172.23.6.x)
        - Nome da máquina
        - Nome do usuário
        
        Retorna None se o IP não estiver na faixa 172.23.6.x
        """
        try:
            # Pega o nome da máquina
            nome_maquina = socket.gethostname()
            
            # Pega o nome do usuário
            nome_usuario = getpass.getuser()
            
            # Pega o IP local
            try:
                # Método mais confiável: conecta a um socket externo sem realmente enviar dados
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(("8.8.8.8", 80))
                ip_local = s.getsockname()[0]
                s.close()
            except Exception:
                # Fallback: usar localhost
                ip_local = socket.gethostbyname(socket.gethostname())
            
            # Verifica se o IP está no prefixo 172.23.6.x
            if not ip_local.startswith("172.23.6."):
                # IP fora da faixa gerenciada, desconsiderar
                return None
            
            return {
                'ip': ip_local,
                'nome_maquina': nome_maquina,
                'nome_usuario': nome_usuario
            }
        except Exception as e:
            QMessageBox.warning(self, "Erro", f"Não foi possível obter informações da máquina: {e}")
            return None

    def abrir_form_ip(self, ip_texto=None):
        if not hasattr(self, 'ip_controller') or not self.ip_controller:
            return

        ip_inicial = ip_texto
        if not ip_inicial and hasattr(self, 'table_ips') and self.table_ips.currentRow() >= 0:
            item = self.table_ips.item(self.table_ips.currentRow(), 0)
            if item:
                ip_inicial = item.text()
        if not ip_inicial:
            ip_inicial = "172.23.6.1"

        registro = self.ip_controller.buscar_por_ip(ip_inicial)

        dialog = QDialog(self)
        dialog.setWindowTitle("Alocar/Editar IP")
        dialog.setFixedSize(1040, 620)
        form_layout = QVBoxLayout(dialog)
        form_layout.setSpacing(10)

        form_layout.addWidget(QLabel("<b>IP</b>"))
        combo_ip = QComboBox()
        combo_ip.addItems([f"172.23.6.{i}" for i in range(1, 256)])
        combo_ip.setCurrentText(ip_inicial)
        combo_ip.setMinimumWidth(900)
        form_layout.addWidget(combo_ip)

        form_layout.addWidget(QLabel("<b>Máquina</b>"))
        txt_ip_maquina = QLineEdit()
        txt_ip_maquina.setPlaceholderText("Ex.: Desktop / Notebook / Servidor")
        txt_ip_maquina.setMinimumWidth(900)
        form_layout.addWidget(txt_ip_maquina)

        form_layout.addWidget(QLabel("<b>Nome da máquina</b>"))
        txt_ip_nome_maquina = QLineEdit()
        txt_ip_nome_maquina.setPlaceholderText("Ex.: PC-ADMIN-01")
        txt_ip_nome_maquina.setMinimumWidth(900)
        form_layout.addWidget(txt_ip_nome_maquina)

        form_layout.addWidget(QLabel("<b>Nome do usuário</b>"))
        txt_ip_nome_usuario = QLineEdit()
        txt_ip_nome_usuario.setPlaceholderText("Nome do responsável pelo IP")
        txt_ip_nome_usuario.setMinimumWidth(900)
        form_layout.addWidget(txt_ip_nome_usuario)

        # Botão para buscar informações da máquina
        def preencer_informacoes_maquina():
            """Busca as informações da máquina local e preenche o formulário"""
            info = self.obter_informacoes_maquina()
            if info:
                # Preenche os campos automaticamente
                txt_ip_nome_usuario.setText(info['nome_usuario'])
                txt_ip_nome_maquina.setText(info['nome_maquina'])
                # Seleciona o IP na lista
                combo_ip.setCurrentText(info['ip'])
                QMessageBox.information(self, "Sucesso", "Informações da máquina carregadas com sucesso!")
            else:
                QMessageBox.warning(self, "Aviso", "O IP local da máquina não está na faixa 172.23.6.x gerenciada.\nVerifique a configuração de rede.")

        btn_buscar_info = QPushButton("📡 Buscar Informações da Máquina")
        btn_buscar_info.setMinimumWidth(900)
        btn_buscar_info.setObjectName("Info")
        btn_buscar_info.clicked.connect(preencer_informacoes_maquina)
        form_layout.addWidget(btn_buscar_info)
        form_layout.addSpacing(10)

        form_layout.addWidget(QLabel("<b>Setor</b>"))
        combo_ip_setor = QComboBox()
        combo_ip_setor.addItem("-")
        combo_ip_setor.addItems(LISTA_SETORES)
        combo_ip_setor.setMinimumWidth(900)
        form_layout.addWidget(combo_ip_setor)

        form_layout.addWidget(QLabel("<b>Status</b>"))
        combo_ip_status = QComboBox()
        combo_ip_status.addItems(self.ip_statuses)
        combo_ip_status.setMinimumWidth(900)
        form_layout.addWidget(combo_ip_status)

        lbl_ip_modificacao = QLabel("<b>Data de modificação:</b> -")
        form_layout.addWidget(lbl_ip_modificacao)

        if registro:
            txt_ip_maquina.setText(registro.maquina or "")
            txt_ip_nome_maquina.setText(registro.nome_maquina or "")
            txt_ip_nome_usuario.setText(registro.nome_usuario or "")
            combo_ip_setor.setCurrentText(registro.setor or "-")
            combo_ip_status.setCurrentText(registro.status or "Livre")
            lbl_ip_modificacao.setText(f"<b>Data de modificação:</b> {registro.data_modificacao or '-'}")

        def atualizar_form_por_ip():
            atual = self.ip_controller.buscar_por_ip(combo_ip.currentText())
            if not atual:
                txt_ip_maquina.clear()
                txt_ip_nome_maquina.clear()
                txt_ip_nome_usuario.clear()
                combo_ip_setor.setCurrentIndex(0)
                combo_ip_status.setCurrentIndex(0)
                lbl_ip_modificacao.setText("<b>Data de modificação:</b> -")
                return
            txt_ip_maquina.setText(atual.maquina or "")
            txt_ip_nome_maquina.setText(atual.nome_maquina or "")
            txt_ip_nome_usuario.setText(atual.nome_usuario or "")
            combo_ip_setor.setCurrentText(atual.setor or "-")
            combo_ip_status.setCurrentText(atual.status or "Livre")
            lbl_ip_modificacao.setText(f"<b>Data de modificação:</b> {atual.data_modificacao or '-'}")

        combo_ip.currentTextChanged.connect(lambda _: atualizar_form_por_ip())

        btn_row = QHBoxLayout()
        btn_salvar_ip = QPushButton("Salvar alocação")
        btn_salvar_ip.setObjectName("SubmitBtn")
        btn_liberar_ip = QPushButton("Liberar IP")
        btn_liberar_ip.setObjectName("Danger")
        btn_fechar = QPushButton("Fechar")

        def salvar_no_dialog():
            try:
                setor = combo_ip_setor.currentText()
                if setor == "-":
                    setor = ""

                self.ip_controller.salvar_ip(
                    combo_ip.currentText().strip(),
                    txt_ip_maquina.text().strip(),
                    txt_ip_nome_maquina.text().strip(),
                    txt_ip_nome_usuario.text().strip(),
                    setor,
                    combo_ip_status.currentText(),
                )
                self.load_ips()
                atualizar_form_por_ip()
                QMessageBox.information(self, "Sucesso", "IP atualizado com sucesso!")
            except Exception as e:
                QMessageBox.warning(self, "Erro", str(e))

        def liberar_no_dialog():
            try:
                self.ip_controller.liberar_ip(combo_ip.currentText().strip())
                self.load_ips()
                atualizar_form_por_ip()
                QMessageBox.information(self, "Sucesso", "IP liberado com sucesso!")
            except Exception as e:
                QMessageBox.warning(self, "Erro", str(e))

        btn_salvar_ip.clicked.connect(salvar_no_dialog)
        btn_liberar_ip.clicked.connect(liberar_no_dialog)
        btn_fechar.clicked.connect(dialog.close)

        btn_row.addWidget(btn_salvar_ip)
        btn_row.addWidget(btn_liberar_ip)
        btn_row.addWidget(btn_fechar)
        form_layout.addLayout(btn_row)
        form_layout.addStretch()

        dialog.exec()

    def _ip_selecionado_na_tabela(self):
        if not hasattr(self, 'table_ips') or self.table_ips.currentRow() < 0:
            return None
        item = self.table_ips.item(self.table_ips.currentRow(), 0)
        return item.text() if item else None

    def _selecionar_linha_por_ip(self, ip_texto):
        if not hasattr(self, 'table_ips') or not ip_texto:
            return
        for row in range(self.table_ips.rowCount()):
            cell = self.table_ips.item(row, 0)
            if cell and cell.text() == ip_texto:
                self.table_ips.selectRow(row)
                return

    def liberar_ip(self, ip_texto=None):
        try:
            ip_alvo = ip_texto or self._ip_selecionado_na_tabela()
            if not ip_alvo:
                raise ValueError("Selecione um IP para liberar.")
            self.ip_controller.liberar_ip(ip_alvo)
            self.load_ips()
            self._selecionar_linha_por_ip(ip_alvo)
            QMessageBox.information(self, "Sucesso", "IP liberado com sucesso!")
        except Exception as e:
            QMessageBox.warning(self, "Erro", str(e))

    def load_users(self):
        if not hasattr(self, 'auth_controller'): return
        termo = self.txt_search_user.text()
        setor = self.combo_filter_setor.currentText()
        incluir_inativos = self.check_incluir_inativos.isChecked()
        usuarios = self.auth_controller.listar_usuarios(termo, setor, incluir_inativos)
        self.table_users.setRowCount(len(usuarios))
        for i, u in enumerate(usuarios):
            is_active = getattr(u, 'ativo', True)

            # Coluna Nome
            nome_display = u.nome
            if u.tipo == 1: nome_display += " (Admin)"
            elif u.tipo == 2: nome_display += ""
            elif u.tipo == 3: nome_display += " (Responsável)"
            if not is_active: nome_display += " (Inativo)"
            nome_item = QTableWidgetItem(nome_display)

            # Colunas Login e Setor
            login_item = QTableWidgetItem(u.login)
            setor_item = QTableWidgetItem(u.setor or "-")

            if not is_active:
                gray_color = QColor("gray")
                nome_item.setForeground(gray_color)
                login_item.setForeground(gray_color)
                setor_item.setForeground(gray_color)

            self.table_users.setItem(i, 0, nome_item)
            self.table_users.setItem(i, 1, login_item)
            self.table_users.setItem(i, 2, setor_item)
            
            btn_edit = QPushButton("Editar"); btn_edit.setFixedSize(90, 36)
            btn_edit.clicked.connect(lambda _, user=u: self.editar_usuario(user))
            btn_del = QPushButton("Excluir"); btn_del.setObjectName("Danger"); btn_del.setFixedSize(90, 36)
            btn_del.clicked.connect(lambda _, uid=u.id: self.excluir_usuario(uid))
            
            # Desabilitar ações para usuários inativos
            if not is_active:
                btn_edit.setEnabled(False)
                btn_del.setEnabled(False)

            container = QWidget(); l = QHBoxLayout(container); l.setContentsMargins(2,2,2,2)
            l.addWidget(btn_edit); l.addWidget(btn_del); self.table_users.setCellWidget(i, 3, container)

    def editar_usuario(self, user):
        dialog = UserEditDialog(self.auth_controller, user, self)
        dialog.exec()
        self.load_users()

    def abrir_cadastro_usuario(self):
        dialog = UserRegisterDialog(self.auth_controller, self)
        dialog.exec()
        self.load_users()

    def excluir_usuario(self, user_id):
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Desativar Usuário")
        msg_box.setText("Tem certeza que deseja desativar este usuário?")
        msg_box.setIcon(QMessageBox.Question)
        msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg_box.button(QMessageBox.Yes).setText("Sim")
        msg_box.button(QMessageBox.No).setText("Não")
        msg_box.setDefaultButton(QMessageBox.No)
        confirm = msg_box.exec()

        if confirm == QMessageBox.Yes:
            try: self.auth_controller.excluir_usuario(user_id); self.load_users()
            except Exception as e: QMessageBox.warning(self, "Erro", str(e))

    def prev_page_historico(self):
        if self.current_page_historico > 1:
            self.current_page_historico -= 1
            self.refresh_data()

    def next_page_historico(self):
        if self.current_page_historico < self.total_pages_historico:
            self.current_page_historico += 1
            self.refresh_data()

    def refresh_data(self):
        current_idx = self.pages.currentIndex()
        try:            
            # Busca as solicitações pendentes para atualizar o contador e, se necessário, a tabela.
            solicitacoes_pendentes = []
            if hasattr(self, 'solicitacao_controller') and self.solicitacao_controller:
                try:
                    solicitacoes_pendentes = self.solicitacao_controller.listar_pendentes()
                except Exception as e:
                    print(f"Erro ao listar solicitações pendentes: {e}")
            count = len(solicitacoes_pendentes)

            # Atualiza o badge
            if count > 0:
                self.lbl_accounts_count.setText(str(count))
                self.lbl_accounts_count.setVisible(True)
            else:
                self.lbl_accounts_count.setVisible(False)

            # Atualiza a tabela da aba ativa
            if current_idx == 0:
                v_scroll = self.page_work['table'].verticalScrollBar().value()
                chamados = self.controller.listar_pendentes()
                self.preencher_tabela_admin(self.page_work['table'], chamados, edit_mode=True)
                self.page_work['table'].verticalScrollBar().setValue(v_scroll)
            elif current_idx == 1:
                # 1. Buscar todos os chamados
                chamados = self.controller.listar_todos()
                for c in chamados:
                    c.tipo_item = 'chamado'

                # 2. Buscar todas as solicitações (se o controller estiver disponível)
                solicitacoes = []
                if hasattr(self, 'solicitacao_controller') and self.solicitacao_controller:
                    try:
                        solicitacoes = self.solicitacao_controller.listar_todas_solicitacoes()
                    except Exception as e:
                        print(f"Erro ao listar todas solicitações: {e}")
                for s in solicitacoes:
                    s.tipo_item = 'solicitacao'
                    s.maquina = "Solicitação de acesso"
                    s.descricao = s.sistemas_solicitados
                
                # 3. Unir e ordenar
                todos_itens = chamados + solicitacoes
                todos_itens.sort(key=lambda x: getattr(x, 'data_abertura', ''), reverse=True)

                total_items = len(todos_itens)
                self.total_pages_historico = (total_items + self.items_per_page - 1) // self.items_per_page or 1

                if self.current_page_historico > self.total_pages_historico:
                    self.current_page_historico = self.total_pages_historico

                start_index = (self.current_page_historico - 1) * self.items_per_page
                end_index = start_index + self.items_per_page
                items_for_page = todos_itens[start_index:end_index]

                self.preencher_tabela_admin(self.page_all['table'], items_for_page, edit_mode=False)
                self.page_all['table'].verticalScrollBar().setValue(0)

                # Atualiza controles da paginação
                self.page_all['lbl_page'].setText(f"Página {self.current_page_historico} / {self.total_pages_historico}")
                self.page_all['btn_prev'].setEnabled(self.current_page_historico > 1)
                self.page_all['btn_next'].setEnabled(self.current_page_historico < self.total_pages_historico)
            elif current_idx == 2:
                # Reutiliza a busca já feita para o contador
                self.preencher_tabela_solicitacoes(self.page_accounts['table'], solicitacoes_pendentes)
        except Exception as e: print(f"Erro refresh: {e}")

    def preencher_tabela_admin(self, table, chamados, edit_mode):
        table.setRowCount(len(chamados))
        def parse_date(date_str):
            try: return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
            except: return None
        agora = datetime.now()
        for i, c in enumerate(chamados):
            dt_obj = parse_date(c.data_abertura)
            bg_color = None; fg_color = None; border_style = ""
            if dt_obj:
                diff = (agora - dt_obj).total_seconds()
                if diff < 16:
                    cycle = diff % 4 
                    if cycle < 2: bg_color = QColor("#d32f2f"); fg_color = QColor("white")
                    else: bg_color = QColor("white"); fg_color = QColor("#d32f2f"); border_style = "border: 1px solid #d32f2f;"
            
            table.setItem(i, 0, QTableWidgetItem(c.setor_usuario))
            table.setItem(i, 1, QTableWidgetItem(c.nome_usuario))
            table.setItem(i, 2, QTableWidgetItem(c.maquina or "N/A"))
            
            dt = parse_date(c.data_abertura)
            hora, data = ("", c.data_abertura)
            if dt: hora, data = dt.strftime('%H:%M'), dt.strftime('%d/%m/%y')
            h_item = QTableWidgetItem(hora); h_item.setTextAlignment(Qt.AlignCenter); table.setItem(i, 3, h_item)
            d_item = QTableWidgetItem(data); d_item.setTextAlignment(Qt.AlignCenter); table.setItem(i, 4, d_item)
            
            table.setItem(i, 5, QTableWidgetItem(c.descricao))
            status_item = QTableWidgetItem(c.status); status_item.setTextAlignment(Qt.AlignCenter)
            font = QFont(); font.setBold(True); status_item.setFont(font)
            if c.status == "Aberto": status_item.setForeground(QColor("#d32f2f"))
            elif c.status == "Em espera": status_item.setForeground(QColor("#757575"))
            elif c.status == "Resolvido": status_item.setForeground(QColor("#2196F3"))
            elif c.status == "Finalizado": status_item.setForeground(QColor("#2E7D32"))
            else: status_item.setForeground(QColor("#F57C00"))
            table.setItem(i, 6, status_item)
            
            if edit_mode:
                btn = QPushButton(); btn.setFixedSize(180, 36) # Aumentado para caber textos longos
                is_mine = (c.suporte_id == self.user.id)
                is_locked = ((c.status == "Em andamento" or c.status == "Em espera") and not is_mine)
                if c.status == "Aberto": btn.setText("Atender"); btn.setObjectName("Info"); btn.setEnabled(True)
                elif is_locked: btn.setText("Bloqueado"); btn.setEnabled(False)
                elif c.status == "Resolvido": btn.setText("Detalhes"); btn.setObjectName("Info"); btn.setEnabled(True)
                else: btn.setText("Continuar"); btn.setObjectName("SubmitBtn"); btn.setEnabled(True)
                if not is_locked and c.status not in ['Resolvido', 'Finalizado']: btn.clicked.connect(lambda _, cid=c.id: self.abrir_atendimento(cid))
                elif c.status == 'Resolvido': btn.clicked.connect(lambda _, cid=c.id, ctype='chamado': self.ver_detalhes_unificado_admin(cid, ctype))
                
                widget = QWidget(); layout = QHBoxLayout(widget); layout.setContentsMargins(5, 5, 5, 5); layout.addWidget(btn)
                if bg_color:
                    bg_hex = bg_color.name(); fg_hex = fg_color.name()
                    widget.setStyleSheet(f"background-color: transparent;")
                    btn.setStyleSheet(f"background-color: {bg_hex}; color: {fg_hex}; {border_style} border-radius: 4px; font-weight: bold;")
                
                table.setCellWidget(i, 7, widget)
            else: 
                btn_details = QPushButton("Detalhes")
                btn_details.setObjectName("Info")
                btn_details.setFixedSize(100, 36)
                item_type = getattr(c, 'tipo_item', 'chamado')
                btn_details.clicked.connect(lambda _, cid=c.id, ctype=item_type: self.ver_detalhes_unificado_admin(cid, ctype))
                
                widget = QWidget(); layout = QHBoxLayout(widget); layout.setContentsMargins(5, 5, 5, 5); layout.addWidget(btn_details)
                table.setCellWidget(i, 7, widget)

    def abrir_atendimento(self, chamado_id):
        self.timer.stop()
        reopen_dialog = True
        while reopen_dialog:
            dialog = TicketActionDialog(chamado_id, self.controller, self.user, self)
            dialog.exec()
            reopen_dialog = getattr(dialog, 'reopen_requested', False)
        self.timer.start(1000)
        self.refresh_data()

    def ver_detalhes_unificado_admin(self, item_id, item_type):
        if item_type == 'chamado':
            self.ver_detalhes_chamado_admin(item_id)
        elif item_type == 'solicitacao':
            self.abrir_atendimento_solicitacao(item_id)

    def preencher_tabela_solicitacoes(self, table, solicitacoes):
        table.setRowCount(len(solicitacoes))
        def parse_date(date_str):
            try: return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
            except: return None

        for i, s in enumerate(solicitacoes):
            table.setItem(i, 0, QTableWidgetItem(s.setor_usuario))
            table.setItem(i, 1, QTableWidgetItem(s.nome_usuario))
            table.setItem(i, 2, QTableWidgetItem(s.sistemas_solicitados))

            dt = parse_date(s.data_abertura)
            hora, data = ("", s.data_abertura)
            if dt: hora, data = dt.strftime('%H:%M'), dt.strftime('%d/%m/%y')
            h_item = QTableWidgetItem(hora); h_item.setTextAlignment(Qt.AlignCenter); table.setItem(i, 3, h_item)
            d_item = QTableWidgetItem(data); d_item.setTextAlignment(Qt.AlignCenter); table.setItem(i, 4, d_item)

            status_item = QTableWidgetItem(s.status); status_item.setTextAlignment(Qt.AlignCenter)
            font = QFont(); font.setBold(True); status_item.setFont(font)
            if s.status == "Aberto": status_item.setForeground(QColor("#d32f2f"))
            elif s.status == "Em espera": status_item.setForeground(QColor("#757575"))
            else: status_item.setForeground(QColor("#F57C00"))
            table.setItem(i, 5, status_item)

            btn = QPushButton(); btn.setFixedSize(180, 36) # Aumentado para consistência e textos longos
            is_mine = (s.suporte_id == self.user.id)
            is_locked = ((s.status == "Em andamento" or s.status == "Em espera") and not is_mine)
            if s.status == "Aberto": btn.setText("Atender"); btn.setObjectName("Info"); btn.setEnabled(True)
            elif is_locked: btn.setText("Bloqueado"); btn.setEnabled(False)
            elif s.status == "Resolvido": btn.setText("Detalhes"); btn.setObjectName("Info"); btn.setEnabled(True)
            else: btn.setText("Continuar"); btn.setObjectName("SubmitBtn"); btn.setEnabled(True)
            if not is_locked and s.status not in ['Resolvido', 'Finalizado']: btn.clicked.connect(lambda _, sid=s.id: self.abrir_atendimento_solicitacao(sid))
            elif s.status == 'Resolvido': btn.clicked.connect(lambda _, sid=s.id, stype='solicitacao': self.ver_detalhes_unificado_admin(sid, stype))

            widget = QWidget(); layout = QHBoxLayout(widget); layout.setContentsMargins(5, 5, 5, 5); layout.addWidget(btn)
            table.setCellWidget(i, 6, widget)

    def abrir_atendimento_solicitacao(self, solicitacao_id):
        self.timer.stop()
        if not hasattr(self, 'solicitacao_controller') or not self.solicitacao_controller:
            QMessageBox.warning(self, "Erro", "Controlador de solicitações não inicializado.")
            self.timer.start(1000)
            return
        reopen_dialog = True
        while reopen_dialog:
            dialog = AccountRequestActionDialog(solicitacao_id, self.solicitacao_controller, self.user, self)
            dialog.exec()
            reopen_dialog = getattr(dialog, 'reopen_requested', False)
        self.timer.start(1000)
        self.refresh_data()

    def ver_detalhes_chamado_admin(self, chamado_id):
        try:
            chamado = self.controller.buscar_por_id(chamado_id)
            if not chamado:
                QMessageBox.warning(self, "Erro", "Chamado não encontrado!")
                return
            
            dialog = QDialog(self)
            dialog.setWindowTitle(f"Detalhes do Chamado #{chamado_id}")
            dialog.setFixedSize(600, 650)
            dialog.setStyleSheet("background-color: #f0f3f4;")
            
            layout = QVBoxLayout(dialog)
            
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setStyleSheet("border: none;")
            scroll_content = QWidget()
            scroll_content.setStyleSheet("background-color: #f0f3f4;")
            scroll_layout = QVBoxLayout(scroll_content)
            
            header_info = f"<h3 style='margin:0; color:#2c3e50;'>Chamado #{chamado.id} - {chamado.maquina}</h3>"
            lbl_header = QLabel(header_info)
            scroll_layout.addWidget(lbl_header)
            scroll_layout.addSpacing(10)
            
            scroll_layout.addWidget(QLabel("<b style='font-size: 13px; color: #333;'>Descrição:</b>"))
            lbl_desc = QLabel(chamado.descricao)
            lbl_desc.setWordWrap(True)
            lbl_desc.setStyleSheet("background-color:#f5f5f5; padding:10px; border-radius:4px; border:1px solid #ddd;")
            scroll_layout.addWidget(lbl_desc)
            scroll_layout.addSpacing(15)
            
            # --- BOTÃO PARA VER IMAGEM ANEXADA ---
            if hasattr(chamado, 'imagem_data') and chamado.imagem_data:
                from .dialogs import ImageViewDialog
                btn_view_img = QPushButton("🖼️ Ver Imagem Anexada")
                btn_view_img.setObjectName("Info")
                btn_view_img.setStyleSheet("background-color: #2196F3; color: white; padding: 8px; border-radius: 4px; font-weight: bold;")
                btn_view_img.clicked.connect(lambda: ImageViewDialog(chamado.imagem_data, getattr(chamado, 'imagem_filename', 'imagem.png'), dialog).exec())
                scroll_layout.addWidget(btn_view_img)
                scroll_layout.addSpacing(15)
            
            dates_card = QFrame()
            dates_card.setStyleSheet("background-color: white; border: 1px solid #ddd; border-radius: 4px; padding: 10px;")
            dates_layout = QVBoxLayout(dates_card)
            dates_layout.setSpacing(8)
            
            dates_layout.addWidget(QLabel("<b style='color: #2c3e50;'>Linhas do Tempo:</b>"))
            
            def format_datetime(dt_str):
                try:
                    dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
                    return dt.strftime("%d/%m/%Y às %H:%M:%S")
                except:
                    return dt_str if dt_str else "-"
            
            data_abertura = format_datetime(chamado.data_abertura)
            dates_layout.addWidget(QLabel(f"<b>📅 Aberto:</b> {data_abertura}"))
            
            if chamado.data_inicio_atendimento:
                data_inicio = format_datetime(chamado.data_inicio_atendimento)
                dates_layout.addWidget(QLabel(f"<b>⏱️ Atendimento Iniciado:</b> {data_inicio}"))
            
            if chamado.data_fechamento:
                data_fechamento = format_datetime(chamado.data_fechamento)
                dates_layout.addWidget(QLabel(f"<b>✓ Finalizado:</b> {data_fechamento}"))
            
            scroll_layout.addWidget(dates_card)
            scroll_layout.addSpacing(15)
            
            if chamado.diagnostico:
                scroll_layout.addWidget(QLabel("<b style='font-size: 13px; color: #333;'>Diagnóstico:</b>"))
                lbl_diag = QLabel(chamado.diagnostico)
                lbl_diag.setWordWrap(True)
                lbl_diag.setStyleSheet("background-color:#f0f8ff; padding:10px; border-radius:4px; border:1px solid #87ceeb;")
                scroll_layout.addWidget(lbl_diag)
                scroll_layout.addSpacing(15)
            
            if chamado.solucao:
                scroll_layout.addWidget(QLabel("<b style='font-size: 13px; color: #333;'>Solução Aplicada:</b>"))
                lbl_sol = QLabel(chamado.solucao)
                lbl_sol.setWordWrap(True)
                lbl_sol.setStyleSheet("background-color:#fff3cd; padding:10px; border-radius:4px; border:1px solid #ffc107;")
                lbl_sol.setTextInteractionFlags(Qt.TextSelectableByMouse)
                scroll_layout.addWidget(lbl_sol)
            
            scroll_layout.addStretch()
            scroll.setWidget(scroll_content)
            layout.addWidget(scroll)
            
            # Removido botão de fechar redundante — diálogo já fecha pelo botão padrão
            
            dialog.exec()
        except Exception as e:
            QMessageBox.warning(self, "Erro", f"Erro ao abrir detalhes: {str(e)}")