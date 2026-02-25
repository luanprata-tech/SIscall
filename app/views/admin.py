# views/admin.py
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QLabel, 
    QPushButton, QStackedWidget, QTableWidget, QTableWidgetItem, 
    QHeaderView, QAbstractItemView, QMessageBox, QDialog, 
    QScrollArea, QFrame, QDateEdit, QGroupBox, QGridLayout, 
    QLineEdit, QComboBox
)
from PySide6.QtCore import Qt, QTimer, QDate
from PySide6.QtGui import QIcon, QFont, QColor
from datetime import datetime
from .dialogs import TicketActionDialog, UserEditDialog, UserRegisterDialog, AccountRequestActionDialog

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

    def set_solicitacao_controller(self, solicitacao_controller):
        self.solicitacao_controller = solicitacao_controller

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
        
        self.btn_accounts = QPushButton("Solicitações de Conta"); self.btn_accounts.setObjectName("MenuBtn"); self.btn_accounts.setCheckable(True); self.btn_accounts.clicked.connect(lambda: self.switch_page(2))

        self.btn_reports = QPushButton("Relatórios"); self.btn_reports.setObjectName("MenuBtn"); self.btn_reports.setCheckable(True); self.btn_reports.clicked.connect(lambda: self.switch_page(3))
        self.btn_config = QPushButton("Configurações"); self.btn_config.setObjectName("MenuBtn"); self.btn_config.setIcon(QIcon.fromTheme("preferences-system")); self.btn_config.setCheckable(True); self.btn_config.clicked.connect(lambda: self.switch_page(4))
        btn_logout = QPushButton("Sair"); btn_logout.setObjectName("MenuBtn"); btn_logout.setStyleSheet("color: #ff6b6b;"); btn_logout.clicked.connect(self.logout_callback)

        sidebar_layout.addWidget(lbl_brand); sidebar_layout.addSpacing(20); sidebar_layout.addWidget(self.btn_work); sidebar_layout.addWidget(self.btn_all); sidebar_layout.addWidget(self.btn_accounts); sidebar_layout.addWidget(self.btn_reports); sidebar_layout.addWidget(self.btn_config); sidebar_layout.addStretch(); sidebar_layout.addWidget(btn_logout)

        self.pages = QStackedWidget()
        self.page_work = self.create_table_page("Chamados Pendentes", edit_mode=True)
        self.page_all = self.create_table_page("Histórico Completo", edit_mode=False)
        self.page_accounts = self.create_accounts_table_page()
        self.page_reports = self.create_reports_page() # Será o índice 3 agora
        self.page_config_widget = self.create_config_page()

        self.pages.addWidget(self.page_work['widget'])
        self.pages.addWidget(self.page_all['widget'])
        self.pages.addWidget(self.page_accounts['widget'])
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
        table.horizontalHeader().setSectionResizeMode(6, QHeaderView.Stretch)
        
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.verticalHeader().setVisible(False) 
        table.verticalHeader().setMinimumSectionSize(70)
        table.verticalHeader().setDefaultSectionSize(70)
        table.setWordWrap(True)
        layout.addWidget(header); layout.addWidget(table)
        return {'widget': widget, 'table': table, 'edit_mode': edit_mode}

    def create_accounts_table_page(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        header = QLabel("Solicitações de Conta Pendentes")
        header.setStyleSheet("font-size: 24px; font-weight: bold; color: #2c3e50; margin: 15px 5px;")
        
        table = QTableWidget()
        table.setAlternatingRowColors(True)
        cols = ["ID", "Setor", "Usuário", "Sistemas Solicitados", "Hora", "Data", "Status", "Ação"]
        table.setColumnCount(len(cols))
        table.setHorizontalHeaderLabels(cols)
        
        table.setColumnWidth(0, 40)
        table.setColumnWidth(1, 150)
        table.setColumnWidth(2, 150)
        table.setColumnWidth(4, 90)
        table.setColumnWidth(5, 90)
        table.setColumnWidth(6, 150)
        table.setColumnWidth(7, 200)
        table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        

        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.verticalHeader().setVisible(False) 
        table.verticalHeader().setMinimumSectionSize(70)
        table.verticalHeader().setDefaultSectionSize(70)
        table.setWordWrap(True)
        
        layout.addWidget(header); layout.addWidget(table)
        return {'widget': widget, 'table': table}

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
        
        btn_new_user = QPushButton("Novo Usuário")
        btn_new_user.setIcon(QIcon.fromTheme("contact-new"))
        btn_new_user.clicked.connect(self.abrir_cadastro_usuario)
        
        filter_layout.addWidget(self.txt_search_user); filter_layout.addWidget(self.combo_filter_setor); filter_layout.addWidget(btn_new_user)
        layout.addLayout(filter_layout)
        
        self.table_users = QTableWidget()
        self.table_users.setAlternatingRowColors(True)
        self.table_users.setColumnCount(5)
        self.table_users.setHorizontalHeaderLabels(["ID", "Nome", "Login", "Setor", "Ações"])
        
        self.table_users.setColumnWidth(0, 60)
        self.table_users.setColumnWidth(2, 150)
        self.table_users.setColumnWidth(3, 200)
        self.table_users.setColumnWidth(4, 320)
        self.table_users.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        
        self.table_users.verticalHeader().setMinimumSectionSize(70) 
        self.table_users.verticalHeader().setDefaultSectionSize(70) 
        self.table_users.verticalHeader().setVisible(False)
        self.table_users.setEditTriggers(QAbstractItemView.NoEditTriggers)
        
        layout.addWidget(self.table_users)
        return widget

    def switch_page(self, index):
        self.pages.setCurrentIndex(index)
        self.btn_work.setChecked(index == 0)
        self.btn_all.setChecked(index == 1)
        self.btn_accounts.setChecked(index == 2)
        self.btn_reports.setChecked(index == 3)
        self.btn_config.setChecked(index == 4)
        if index == 4: self.load_users()
        elif index == 3: pass # Relatórios
        elif index == 2: self.refresh_data()
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

    def abrir_cadastro_usuario(self):
        dialog = UserRegisterDialog(self.auth_controller, self)
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
            elif current_idx == 2:
                solicitacoes = self.solicitacao_controller.listar_pendentes()
                self.preencher_tabela_solicitacoes(self.page_accounts['table'], solicitacoes)
        except Exception as e: print(f"Erro refresh: {e}")

    def preencher_tabela_admin(self, table, chamados, edit_mode):
        v_scroll = table.verticalScrollBar().value()
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
            
            id_item = QTableWidgetItem(str(c.id)); table.setItem(i, 0, id_item)
            table.setItem(i, 1, QTableWidgetItem(c.setor_usuario))
            table.setItem(i, 2, QTableWidgetItem(c.nome_usuario))
            table.setItem(i, 3, QTableWidgetItem(c.maquina or "N/A"))
            
            dt = parse_date(c.data_abertura)
            hora, data = ("", c.data_abertura)
            if dt: hora, data = dt.strftime('%H:%M'), dt.strftime('%d/%m/%y')
            h_item = QTableWidgetItem(hora); h_item.setTextAlignment(Qt.AlignCenter); table.setItem(i, 4, h_item)
            d_item = QTableWidgetItem(data); d_item.setTextAlignment(Qt.AlignCenter); table.setItem(i, 5, d_item)
            
            table.setItem(i, 6, QTableWidgetItem(c.descricao))
            status_item = QTableWidgetItem(c.status); status_item.setTextAlignment(Qt.AlignCenter)
            font = QFont(); font.setBold(True); status_item.setFont(font)
            if c.status == "Aberto": status_item.setForeground(QColor("#d32f2f"))
            elif c.status == "Resolvido": status_item.setForeground(QColor("#2196F3"))
            elif c.status == "Finalizado": status_item.setForeground(QColor("#2E7D32"))
            else: status_item.setForeground(QColor("#F57C00"))
            table.setItem(i, 7, status_item)
            
            if edit_mode:
                btn = QPushButton(); btn.setFixedSize(180, 36) # Aumentado para caber textos longos
                is_mine = (c.suporte_id == self.user.id)
                is_locked = (c.status == "Em andamento" and not is_mine)
                if c.status == "Aberto": btn.setText("Atender"); btn.setObjectName("Info"); btn.setEnabled(True)
                elif is_locked: btn.setText("Bloqueado"); btn.setEnabled(False)
                elif c.status == "Resolvido": btn.setText("Aguardando Usuário"); btn.setEnabled(False)
                else: btn.setText("Continuar"); btn.setObjectName("SubmitBtn"); btn.setEnabled(True)
                if not is_locked and c.status != 'Resolvido': btn.clicked.connect(lambda _, cid=c.id: self.abrir_atendimento(cid))
                
                widget = QWidget(); layout = QHBoxLayout(widget); layout.setContentsMargins(5, 5, 5, 5); layout.addWidget(btn)
                if bg_color:
                    bg_hex = bg_color.name(); fg_hex = fg_color.name()
                    widget.setStyleSheet(f"background-color: transparent;")
                    btn.setStyleSheet(f"background-color: {bg_hex}; color: {fg_hex}; {border_style} border-radius: 4px; font-weight: bold;")
                
                table.setCellWidget(i, 8, widget)
            else: 
                btn_details = QPushButton("Detalhes")
                btn_details.setObjectName("Info")
                btn_details.setFixedSize(100, 36)
                btn_details.clicked.connect(lambda _, cid=c.id: self.ver_detalhes_chamado_admin(cid))
                
                widget = QWidget(); layout = QHBoxLayout(widget); layout.setContentsMargins(5, 5, 5, 5); layout.addWidget(btn_details)
                table.setCellWidget(i, 8, widget)
        table.verticalScrollBar().setValue(v_scroll)

    def abrir_atendimento(self, chamado_id):
        self.timer.stop()
        dialog = TicketActionDialog(chamado_id, self.controller, self.user, self)
        dialog.exec()
        self.timer.start(1000)
        self.refresh_data()

    def preencher_tabela_solicitacoes(self, table, solicitacoes):
        table.setRowCount(len(solicitacoes))
        def parse_date(date_str):
            try: return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
            except: return None

        for i, s in enumerate(solicitacoes):
            table.setItem(i, 0, QTableWidgetItem(str(s.id)))
            table.setItem(i, 1, QTableWidgetItem(s.setor_usuario))
            table.setItem(i, 2, QTableWidgetItem(s.nome_usuario))
            table.setItem(i, 3, QTableWidgetItem(s.sistemas_solicitados))

            dt = parse_date(s.data_abertura)
            hora, data = ("", s.data_abertura)
            if dt: hora, data = dt.strftime('%H:%M'), dt.strftime('%d/%m/%y')
            h_item = QTableWidgetItem(hora); h_item.setTextAlignment(Qt.AlignCenter); table.setItem(i, 4, h_item)
            d_item = QTableWidgetItem(data); d_item.setTextAlignment(Qt.AlignCenter); table.setItem(i, 5, d_item)

            status_item = QTableWidgetItem(s.status); status_item.setTextAlignment(Qt.AlignCenter)
            font = QFont(); font.setBold(True); status_item.setFont(font)
            if s.status == "Aberto": status_item.setForeground(QColor("#d32f2f"))
            else: status_item.setForeground(QColor("#F57C00"))
            table.setItem(i, 6, status_item)

            btn = QPushButton(); btn.setFixedSize(180, 36) # Aumentado para consistência e textos longos
            is_mine = (s.suporte_id == self.user.id)
            is_locked = (s.status == "Em andamento" and not is_mine)
            if s.status == "Aberto": btn.setText("Atender"); btn.setObjectName("Info"); btn.setEnabled(True)
            elif is_locked: btn.setText("Bloqueado"); btn.setEnabled(False)
            else: btn.setText("Continuar"); btn.setObjectName("SubmitBtn"); btn.setEnabled(True)
            if not is_locked: btn.clicked.connect(lambda _, sid=s.id: self.abrir_atendimento_solicitacao(sid))

            widget = QWidget(); layout = QHBoxLayout(widget); layout.setContentsMargins(5, 5, 5, 5); layout.addWidget(btn)
            table.setCellWidget(i, 7, widget)

    def abrir_atendimento_solicitacao(self, solicitacao_id):
        self.timer.stop()
        dialog = AccountRequestActionDialog(solicitacao_id, self.solicitacao_controller, self.user, self)
        dialog.exec()
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
            
            btn_close = QPushButton("Fechar")
            btn_close.clicked.connect(dialog.accept)
            layout.addWidget(btn_close)
            
            dialog.exec()
        except Exception as e:
            QMessageBox.warning(self, "Erro", f"Erro ao abrir detalhes: {str(e)}")