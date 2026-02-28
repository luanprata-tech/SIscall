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
import json

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
        
        self.items_per_page = 15
        self.current_page_meus_chamados = 1
        self.total_pages_meus_chamados = 1

        
        self.setup_ui()
        self.switch_page(1)
        QTimer.singleShot(100, self.showMaximized)

        # Timer para atualização automática da lista de chamados
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.auto_refresh_data)
        self.refresh_timer.start(5000) # Atualiza a cada 5 segundos


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
            "INTERNET", "SCANNER", "Gestão de Contas", "Outro Dispositivo"
        ])
        self.combo_machine.currentIndexChanged.connect(self.on_machine_changed)
        form_layout.addWidget(self.combo_machine)

        self.contas_container = QWidget()
        self.contas_layout = QVBoxLayout(self.contas_container)
        self.contas_layout.setSpacing(8)
        
        self.contas_label = QLabel("Selecione os sistemas para os quais precisa de acesso:")
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
        is_conta = self.combo_machine.currentText() == "Gestão de Contas"
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
        self.table.setColumnCount(6) 
        self.table.setHorizontalHeaderLabels(["Hora", "Data", "Máquina", "Descrição", "Status", "Ação"])
        
        self.table.setColumnWidth(0, 90) 
        self.table.setColumnWidth(1, 90)
        self.table.setColumnWidth(2, 200)
        self.table.setColumnWidth(4, 120) 
        self.table.setColumnWidth(5, 320) # Aumentado para caber os botões de confirmação e detalhes
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.verticalHeader().setVisible(False) 
        self.table.verticalHeader().setMinimumSectionSize(70)
        self.table.verticalHeader().setDefaultSectionSize(70)
        self.table.setWordWrap(True)
        
        layout.addWidget(header)
        layout.addWidget(self.table)

        # --- WIDGET DE PAGINAÇÃO ---
        self.pagination_widget = QWidget()
        pagination_layout = QHBoxLayout(self.pagination_widget)
        self.btn_prev = QPushButton("<< Anterior")
        self.btn_prev.clicked.connect(self.prev_page)
        self.lbl_page = QLabel("Página 1 / 1")
        self.lbl_page.setAlignment(Qt.AlignCenter)
        self.btn_next = QPushButton("Próximo >>")
        self.btn_next.clicked.connect(self.next_page)

        pagination_layout.addStretch()
        pagination_layout.addWidget(self.btn_prev)
        pagination_layout.addWidget(self.lbl_page)
        pagination_layout.addWidget(self.btn_next)
        pagination_layout.addStretch()

        layout.addWidget(self.pagination_widget)
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
        if index == 1:
            self.current_page_meus_chamados = 1
            self.load_data()

    def load_data(self):
        try:
            # 1. Buscar chamados normais
            chamados = self.controller.listar_meus_chamados(self.user.id)
            for c in chamados:
                c.tipo_item = 'chamado'

            # 2. Buscar solicitações de conta (assumindo que o controller tem este método)
            solicitacoes = self.solicitacao_controller.listar_minhas_solicitacoes(self.user.id)
            for s in solicitacoes:
                s.tipo_item = 'solicitacao'
                s.maquina = "Gestão de Contas"  # Atributo para exibição correta na tabela

            # 3. Unir as duas listas
            todos_itens = chamados + solicitacoes

            # 4. Ordenar a lista unificada pela data de abertura
            todos_itens.sort(key=lambda x: getattr(x, 'data_abertura', ''), reverse=True)

            total_items = len(todos_itens)
            self.total_pages_meus_chamados = (total_items + self.items_per_page - 1) // self.items_per_page or 1

            if self.current_page_meus_chamados > self.total_pages_meus_chamados:
                self.current_page_meus_chamados = self.total_pages_meus_chamados

            start_index = (self.current_page_meus_chamados - 1) * self.items_per_page
            end_index = start_index + self.items_per_page
            items_for_page = todos_itens[start_index:end_index]

            self.preencher_tabela(self.table, items_for_page, is_admin=False)
            self.table.verticalScrollBar().setValue(0)

            # Atualiza controles de paginação
            self.lbl_page.setText(f"Página {self.current_page_meus_chamados} / {self.total_pages_meus_chamados}")
            self.btn_prev.setEnabled(self.current_page_meus_chamados > 1)
            self.btn_next.setEnabled(self.current_page_meus_chamados < self.total_pages_meus_chamados)

        except AttributeError:
            # Fallback caso o método 'listar_minhas_solicitacoes' não exista ainda
            chamados = self.controller.listar_meus_chamados(self.user.id)
            self.preencher_tabela(self.table, chamados, is_admin=False)
        except Exception as e:
            print(f"Erro ao carregar dados unificados: {e}")
            QMessageBox.warning(self, "Erro de Carregamento", f"Não foi possível carregar todos os itens: {e}")

    def auto_refresh_data(self):
        """
        Atualiza automaticamente a lista de chamados se a página correspondente
        estiver visível.
        """
        if self.pages.currentIndex() == 1:
            self.load_data()

    def prev_page(self):
        if self.current_page_meus_chamados > 1:
            self.current_page_meus_chamados -= 1
            self.load_data()

    def next_page(self):
        if self.current_page_meus_chamados < self.total_pages_meus_chamados:
            self.current_page_meus_chamados += 1
            self.load_data()

    def preencher_tabela(self, table, chamados, is_admin=False):
        def parse_date(date_str):
            try: return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
            except: return None
            
        table.setRowCount(len(chamados))
        for i, c in enumerate(chamados):
            dt = parse_date(c.data_abertura)
            hora, data = ("", c.data_abertura)
            if dt: hora, data = dt.strftime('%H:%M'), dt.strftime('%d/%m/%y')
            
            h_item = QTableWidgetItem(hora); h_item.setTextAlignment(Qt.AlignCenter); table.setItem(i, 0, h_item)
            d_item = QTableWidgetItem(data); d_item.setTextAlignment(Qt.AlignCenter); table.setItem(i, 1, d_item)
            table.setItem(i, 2, QTableWidgetItem(c.maquina or "N/A"))
            table.setItem(i, 3, QTableWidgetItem(c.descricao))
            
            status_item = QTableWidgetItem(c.status); status_item.setTextAlignment(Qt.AlignCenter)
            font = QFont(); font.setBold(True); status_item.setFont(font)
            
            if c.status == "Aberto": status_item.setForeground(QColor("#d32f2f"))
            elif c.status == "Resolvido": status_item.setForeground(QColor("#2196F3"))
            elif c.status == "Finalizado": status_item.setForeground(QColor("#2E7D32"))
            else: status_item.setForeground(QColor("#F57C00"))
            table.setItem(i, 4, status_item)
            
            if not is_admin:
                cell_widget = QWidget()
                layout = QHBoxLayout(cell_widget)
                layout.setContentsMargins(5,5,5,5)
                layout.setAlignment(Qt.AlignCenter)

                if c.status == "Aberto":
                    btn_del = QPushButton("Excluir"); btn_del.setObjectName("Danger")
                    btn_del.setFixedSize(90, 36)
                    btn_del.clicked.connect(lambda _, cid=c.id, ctype=c.tipo_item: self.deletar_chamado(cid, ctype))
                    layout.addWidget(btn_del)
                elif c.status == "Resolvido":
                    btn_details = QPushButton("Ver Detalhes")
                    btn_details.setObjectName("Info")
                    btn_details.setFixedSize(120, 36)
                    btn_details.clicked.connect(lambda _, cid=c.id, ctype=c.tipo_item: self.ver_detalhes_chamado(cid, ctype))
                    layout.addWidget(btn_details)

                    btn_confirm = QPushButton("Confirmar e Fechar"); btn_confirm.setObjectName("SubmitBtn") 
                    btn_confirm.setFixedSize(180, 36)
                    btn_confirm.clicked.connect(lambda _, cid=c.id, ctype=c.tipo_item: self.confirmar_fechamento(cid, ctype))
                    layout.addWidget(btn_confirm)
                elif c.status == "Finalizado":
                    btn_details = QPushButton("Detalhes")
                    btn_details.setObjectName("Info")
                    btn_details.setFixedSize(90, 36)
                    btn_details.clicked.connect(lambda _, cid=c.id, ctype=c.tipo_item: self.ver_detalhes_chamado(cid, ctype))
                    layout.addWidget(btn_details)
                table.setCellWidget(i, 5, cell_widget)
                

    def criar_chamado(self):
        try:
            maquina = self.combo_machine.currentText()
            descricao = self.txt_desc.toPlainText()
            
            if maquina == "Gestão de Contas":
                contas_selecionadas = [sistema for sistema, cb in self.checkboxes_contas.items() if cb.isChecked()]
                if not contas_selecionadas:
                    raise ValueError("Para uma solicitação de acesso, selecione pelo menos um sistema!")
                self.solicitacao_controller.criar_solicitacao(self.user.id, descricao, contas_selecionadas)
                QMessageBox.information(self, "Sucesso", "Solicitação de acesso registrada!")
            else:
                self.controller.criar_chamado(self.user.id, descricao, maquina)            
                QMessageBox.information(self, "Sucesso", "Chamado registrado!")

            self.txt_desc.clear()
            self.combo_machine.setCurrentIndex(0)
            for cb in self.checkboxes_contas.values():
                cb.setChecked(False)
            self.switch_page(1)
        except ValueError as e:
            QMessageBox.warning(self, "Atenção", str(e))
        except Exception as e:
            QMessageBox.warning(self, "Erro", str(e))

    def deletar_chamado(self, item_id, item_type):
        confirm = QMessageBox.question(self, "Confirmar", "Excluir?", QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            try:
                if item_type == 'chamado':
                    self.controller.excluir_chamado(item_id)
                elif item_type == 'solicitacao':
                    self.solicitacao_controller.excluir_solicitacao(item_id, self.user.id)
                self.load_data()
            except Exception as e: QMessageBox.warning(self, "Erro", str(e))

    def confirmar_fechamento(self, item_id, item_type):
        confirm = QMessageBox.question(self, "Confirmar Resolução", 
                                       "Você confirma que a solicitação foi atendida? Esta ação fechará o item permanentemente.",
                                       QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            try:
                if item_type == 'chamado':
                    self.controller.fechar_chamado_pelo_usuario(item_id, self.user.id)
                elif item_type == 'solicitacao':
                    self.solicitacao_controller.fechar_solicitacao_pelo_usuario(item_id, self.user.id)
                
                QMessageBox.information(self, "Sucesso", "Item fechado com sucesso!")
                self.load_data()
            except Exception as e:
                QMessageBox.warning(self, "Erro", str(e))

    def ver_detalhes_chamado(self, item_id, item_type):
        try:
            item = None
            if item_type == 'chamado':
                item = self.controller.buscar_por_id(item_id)
            elif item_type == 'solicitacao':
                # Assumindo que o método para buscar por ID existe
                item = self.solicitacao_controller.buscar_por_id(item_id)

            if not item:
                QMessageBox.warning(self, "Erro", "Item não encontrado!")
                return
            
            dialog = QDialog(self)
            dialog.setWindowTitle(f"Detalhes do Item #{item_id}")
            dialog.setFixedSize(500, 400)
            dialog.setStyleSheet("background-color: #f0f3f4;")
            
            layout = QVBoxLayout(dialog)
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setStyleSheet("border: none;")
            scroll_content = QWidget()
            scroll_content.setStyleSheet("background-color: #f0f3f4;")
            scroll_layout = QVBoxLayout(scroll_content)
            
            if item_type == 'chamado':
                lbl_desc_title = QLabel("<b>Problema:</b>")
                scroll_layout.addWidget(lbl_desc_title)
                lbl_desc = QLabel(item.descricao)
                lbl_desc.setWordWrap(True)
                lbl_desc.setStyleSheet("background-color:#f5f5f5; padding:10px; border-radius:4px;")
                scroll_layout.addWidget(lbl_desc)
                scroll_layout.addSpacing(15)
                
                if hasattr(item, 'diagnostico') and item.diagnostico:
                    scroll_layout.addWidget(QLabel("<b>Diagnóstico:</b>"))
                    lbl_diag = QLabel(item.diagnostico)
                    lbl_diag.setWordWrap(True)
                    scroll_layout.addWidget(lbl_diag)
                    scroll_layout.addSpacing(15)
                
                if hasattr(item, 'solucao') and item.solucao:
                    scroll_layout.addWidget(QLabel("<b>Solução:</b>"))
                    lbl_sol = QLabel(item.solucao)
                    lbl_sol.setWordWrap(True)
                    lbl_sol.setTextInteractionFlags(Qt.TextSelectableByMouse)
                    scroll_layout.addWidget(lbl_sol)

            elif item_type == 'solicitacao':
                scroll_layout.addWidget(QLabel("<b>Sistemas Solicitados:</b>"))
                sistemas_label = QLabel(item.sistemas_solicitados.replace(',', '\n'))
                sistemas_label.setWordWrap(True)
                sistemas_label.setStyleSheet("background-color:#f5f5f5; padding:10px; border-radius:4px;")
                scroll_layout.addWidget(sistemas_label)
                scroll_layout.addSpacing(15)

                if hasattr(item, 'credenciais_criadas') and item.credenciais_criadas:
                    scroll_layout.addWidget(QLabel("<b>Credenciais Criadas:</b>"))
                    
                    cred_widget = QWidget()
                    cred_widget.setStyleSheet("background-color:#e8f4f8; padding:10px; border-radius:4px; border:1px solid #add8e6;")
                    cred_layout = QVBoxLayout(cred_widget)

                    try:
                        credenciais_data = json.loads(item.credenciais_criadas)
                        for sistema, cred in credenciais_data.items():
                            cred_label = QLabel(f"<b>{sistema}:</b> {cred}")
                            cred_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
                            cred_layout.addWidget(cred_label)
                    except (json.JSONDecodeError, TypeError):
                        cred_label = QLabel(item.credenciais_criadas)
                        cred_label.setWordWrap(True)
                        cred_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
                        cred_layout.addWidget(cred_label)
                    
                    scroll_layout.addWidget(cred_widget)
            
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