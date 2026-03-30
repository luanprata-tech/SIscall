# views/user.py
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QLabel, 
    QPushButton, QStackedWidget, QComboBox, QCheckBox, 
    QPlainTextEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QMessageBox, QDialog, QScrollArea, QLineEdit
)
import os
import sys
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
        # Definir ícone da janela (suporta executável empacotado)
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

        btn_logout = QPushButton("Sair")
        btn_logout.setObjectName("MenuBtn")
        btn_logout.setStyleSheet("color: #ff6b6b;")
        btn_logout.clicked.connect(self.logout_callback)

        sidebar_layout.addWidget(lbl_brand)
        sidebar_layout.addSpacing(20)
        sidebar_layout.addWidget(self.btn_new_ticket)
        sidebar_layout.addWidget(self.btn_my_tickets)
        # Se for responsável, adiciona o botão de cadastro logo abaixo de 'Meus Chamados'
        if hasattr(self, 'btn_register'):
            sidebar_layout.addWidget(self.btn_register)
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
        # Adiciona itens com label (visível) e value (armazenado) separados.
        machines = [
            ("Selecione aqui", "Selecione aqui"),
            ("COMPUTADOR", "COMPUTADOR"),
            ("NOTEBOOK", "NOTEBOOK"),
            ("IMPRESSORA", "IMPRESSORA"),
            ("TELEFONE", "TELEFONE"),
            ("INTERNET", "INTERNET"),
            ("SCANNER", "SCANNER"),
            ("SISTEMA", "SISTEMA"),
            ("Liberação de usuários para acesso ao sistema", "Solicitação de acesso"),
            ("Outro Dispositivo", "Outro Dispositivo")
        ]
        for label, value in machines:
            self.combo_machine.addItem(label, value)
        self.combo_machine.currentIndexChanged.connect(self.on_machine_changed)
        form_layout.addWidget(self.combo_machine)

        self.contas_container = QWidget()
        self.contas_layout = QVBoxLayout(self.contas_container)
        self.contas_layout.setSpacing(8)
        
        self.contas_label = QLabel("Clique no sistema que precisa de acesso:")
        self.contas_label.setStyleSheet("color: #2c3e50; font-weight: bold;")
        self.contas_label.setVisible(False)
        
        self.checkboxes_contas = {}
        sistemas = ["IGESP","EXPRESSO/E-DOC","REDE","SGI","SISGERI","LABWIN","SISCALL"]
        
        for sistema in sistemas:
            cb = QCheckBox(sistema)
            cb.setStyleSheet("QCheckBox { color: #333; background-color: transparent; }")
            self.checkboxes_contas[sistema] = cb
            self.contas_layout.addWidget(cb)
        
        self.contas_container.setVisible(False)
        form_layout.addWidget(self.contas_label)
        form_layout.addWidget(self.contas_container)

        self.lbl_desc = QLabel("Descrição do Problema:")
        form_layout.addWidget(self.lbl_desc)
        self.txt_desc = QPlainTextEdit()
        self.txt_desc.setPlaceholderText("Digite aqui...")
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
        # Verifica pelo valor associado (userData). Para a opção de contas,
        # o value é 'Solicitação de acesso'.
        is_conta = (self.combo_machine.currentData() == "Solicitação de acesso")
        self.contas_label.setVisible(is_conta)
        self.contas_container.setVisible(is_conta)
        # Ajusta o texto do label de descrição quando for solicitação de acesso
        if is_conta:
            try:
                self.lbl_desc.setText("Use o campo abaixo para informar o usuário que deve ser criado ou redefinido:")
                self.txt_desc.setPlaceholderText("Caso selecione Expresso, enviar nome de usuário, CPF e um email para receber a senha provisória.")
            except Exception:
                pass
        else:
            try:
                self.lbl_desc.setText("Descrição do Problema:")
                self.txt_desc.setPlaceholderText("Digite aqui...")
            except Exception:
                pass
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
        self.table.setColumnWidth(5, 250)
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

        form_layout.addWidget(QLabel("Setor:"))
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
                s.maquina = "Solicitação de acesso"  # Atributo para exibição correta na tabela

            # 3. Unir as duas listas
            todos_itens = chamados + solicitacoes

            # 4. Ordenar a lista unificada: primeiro os com status "Resolvido", depois pelos demais por data
            todos_itens.sort(key=lambda x: (x.status == 'Resolvido', getattr(x, 'data_abertura', '')), reverse=True)

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
            
        def is_senha_request(item):
            # treat any solicitacao whose description mentions 'senha' as a password request
            try:
                return item.tipo_item == 'solicitacao' and item.descricao and 'senha' in item.descricao.lower()
            except Exception:
                return False
        
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
                    btn_del.setFixedSize(90, 42)
                    btn_del.clicked.connect(lambda _, cid=c.id, ctype=c.tipo_item: self.deletar_chamado(cid, ctype))
                    layout.addWidget(btn_del)
                elif c.status == "Resolvido":
                    if c.tipo_item == 'solicitacao':
                        btn_confirm = QPushButton("Confirmar Atendimento"); btn_confirm.setObjectName("SubmitBtn") 
                        btn_confirm.setFixedSize(220, 42)
                        btn_confirm.clicked.connect(lambda _, cid=c.id, ctype=c.tipo_item: self.abrir_confirmacao_solicitacao(cid))
                        layout.addWidget(btn_confirm)
                    else:
                        btn_confirm = QPushButton("Confirmar Atendimento"); btn_confirm.setObjectName("SubmitBtn") 
                        btn_confirm.setFixedSize(220, 42)
                        btn_confirm.clicked.connect(lambda _, cid=c.id, ctype=c.tipo_item: self.confirmar_fechamento(cid, ctype))
                        layout.addWidget(btn_confirm)
                elif c.status == "Finalizado":
                    btn_details = QPushButton("Detalhes")
                    btn_details.setObjectName("Info")
                    btn_details.setFixedSize(90, 42)
                    btn_details.clicked.connect(lambda _, cid=c.id, ctype=c.tipo_item: self.ver_detalhes_chamado(cid, ctype))
                    layout.addWidget(btn_details)
                table.setCellWidget(i, 5, cell_widget)
                

    def criar_chamado(self):
        try:
            # Preferir o valor associado (userData) para salvar no banco;
            # se não houver, usa o texto visível.
            maquina = self.combo_machine.currentData() or self.combo_machine.currentText()
            descricao = self.txt_desc.toPlainText()
            
            if maquina == "Solicitação de acesso":
                contas_selecionadas = [sistema for sistema, cb in self.checkboxes_contas.items() if cb.isChecked()]
                if not contas_selecionadas:
                    raise ValueError("Para uma solicitação de acesso, selecione pelo menos um sistema!")
                self.solicitacao_controller.criar_solicitacao(self.user.id, descricao, contas_selecionadas)
                QMessageBox.information(self, "Sucesso", "Solicitação de acesso registrada!")
            
            elif maquina == 'Selecione aqui':
                raise ValueError("Selecione uma máquina/dispositivo")
            
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
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Confirmar Exclusão")
        msg_box.setText("Tem certeza que deseja excluir este item?")
        msg_box.setIcon(QMessageBox.Question)
        msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg_box.button(QMessageBox.Yes).setText("Sim, excluir")
        msg_box.button(QMessageBox.No).setText("Não")
        msg_box.setDefaultButton(QMessageBox.No)
        confirm = msg_box.exec()

        if confirm == QMessageBox.Yes:
            try:
                if item_type == 'chamado':
                    self.controller.excluir_chamado(item_id)
                elif item_type == 'solicitacao':
                    self.solicitacao_controller.excluir_solicitacao(item_id, self.user.id)
                self.load_data()
            except Exception as e: QMessageBox.warning(self, "Erro", str(e))

    def confirmar_fechamento(self, item_id, item_type, dialog=None):
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Confirmar Resolução")
        msg_box.setText("Você confirma que a solicitação foi atendida? Esta ação fechará o item permanentemente.")
        msg_box.setIcon(QMessageBox.Question)
        msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg_box.button(QMessageBox.Yes).setText("Sim, confirmo")
        msg_box.button(QMessageBox.No).setText("Não")
        msg_box.setDefaultButton(QMessageBox.No)
        confirm = msg_box.exec()

        if confirm == QMessageBox.Yes:
            try:
                if item_type == 'chamado':
                    self.controller.fechar_chamado_pelo_usuario(item_id, self.user.id)
                elif item_type == 'solicitacao':
                    self.solicitacao_controller.fechar_solicitacao_pelo_usuario(item_id, self.user.id)
                
                QMessageBox.information(self, "Sucesso", "Item fechado com sucesso!")
                if dialog:
                    dialog.accept()
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
            dialog.setFixedSize(700, 700)
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

                # show note for Expresso password delivery when request is no longer open
                is_expresso = False
                try:
                    if 'EXPRESSO' in item.sistemas_solicitados.upper():
                        is_expresso = True
                    if is_expresso and item.status in ('Resolvido', 'Finalizado'):
                        note = QLabel("A senha provisória do EXPRESSO será enviada para o email fornecido.")
                        note.setStyleSheet("color: #555; font-style: italic;")
                        scroll_layout.addWidget(note)
                        scroll_layout.addSpacing(15)
                except Exception:
                    pass

                # always build credentials block if data exists; filtering occurs later during iteration
                if hasattr(item, 'credenciais_criadas') and item.credenciais_criadas:
                    scroll_layout.addWidget(QLabel("<b>Credenciais:</b>"))
                    
                    # Criar scroll para credenciais
                    cred_scroll = QScrollArea()
                    cred_scroll.setWidgetResizable(True)
                    cred_scroll.setStyleSheet("background-color:#e8f4f8; border: 1px solid #add8e6;")
                    
                    cred_widget = QWidget()
                    cred_widget.setStyleSheet("background-color:#e8f4f8;")
                    cred_layout = QVBoxLayout(cred_widget)
                    cred_layout.setSpacing(10)

                    try:
                        credenciais_data = json.loads(item.credenciais_criadas)
                        for sistema, cred in credenciais_data.items():
                            # skip expresso entry if present
                            if sistema.strip().upper() == 'EXPRESSO':
                                continue
                            # Parsear "login|senha"
                            if '|' in cred:
                                login, senha = cred.split('|', 1)
                            else:
                                login, senha = cred, "***"
                            
                            # Frame para cada sistema
                            system_frame = QWidget()
                            system_frame.setStyleSheet("background-color: white; border: 1px solid #add8e6; border-radius: 4px; padding: 10px;")
                            system_layout = QVBoxLayout(system_frame)
                            system_layout.setSpacing(3)
                            system_layout.setContentsMargins(10, 10, 10, 10)
                            
                            # Título do sistema
                            title = QLabel(f"<b>{sistema}</b>")
                            system_layout.addWidget(title)
                            
                            # Login
                            login_label = QLabel(f"<b>Login:</b> <span style='font-family: monospace; background-color: #f9f9f9; padding: 2px 5px;'>{login}</span>")
                            login_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
                            system_layout.addWidget(login_label)
                            
                            # Senha
                            senha_label = QLabel(f"<b>Senha:</b> <span style='font-family: monospace; background-color: #f9f9f9; padding: 2px 5px;'>{senha}</span>")
                            senha_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
                            system_layout.addWidget(senha_label)
                            
                            cred_layout.addWidget(system_frame)
                    except (json.JSONDecodeError, TypeError):
                        cred_label = QLabel(item.credenciais_criadas)
                        cred_label.setWordWrap(True)
                        cred_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
                        cred_layout.addWidget(cred_label)
                    
                    cred_layout.addStretch()
                    cred_scroll.setWidget(cred_widget)
                    scroll_layout.addWidget(cred_scroll)
            
            scroll_layout.addStretch()
            scroll.setWidget(scroll_content)
            layout.addWidget(scroll)
            
            # if this is a password-type solicitation still needing user confirmation,
            # add a confirm button below the scroll area within the dialog
            try:
                is_senha = False
                if item_type == 'solicitacao' and item.status == 'Resolvido':
                    if hasattr(item, 'descricao') and item.descricao and 'senha' in item.descricao.lower():
                        is_senha = True
                if is_senha:
                    btn = QPushButton("Confirmar Atendimento")
                    btn.setObjectName("SubmitBtn")
                    def do_confirm():
                        self.confirmar_fechamento(item_id, item_type)
                        dialog.accept()
                    btn.clicked.connect(do_confirm)
                    layout.addWidget(btn)
            except Exception:
                pass
            dialog.exec()
        except Exception as e:
            QMessageBox.warning(self, "Erro", f"Erro ao abrir detalhes: {str(e)}")

    def abrir_confirmacao_solicitacao(self, solicitacao_id):
        try:
            item = self.solicitacao_controller.buscar_por_id(solicitacao_id)
            if not item:
                QMessageBox.warning(self, "Erro", "Solicitação não encontrada!")
                return
            
            dialog = QDialog(self)
            dialog.setWindowTitle(f"Confirmar Atendimento da Solicitação #{solicitacao_id}")
            dialog.setFixedSize(700,700)
            dialog.setStyleSheet("background-color: #f0f3f4;")
            
            layout = QVBoxLayout(dialog)
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setStyleSheet("border: none;")
            scroll_content = QWidget()
            scroll_content.setStyleSheet("background-color: #f0f3f4;")
            scroll_layout = QVBoxLayout(scroll_content)
            
            # Detalhes da solicitação
            scroll_layout.addWidget(QLabel("<b>Sistemas Solicitados:</b>"))
            sistemas_label = QLabel(item.sistemas_solicitados.replace(',', '\n'))
            sistemas_label.setWordWrap(True)
            sistemas_label.setStyleSheet("background-color:#f5f5f5; padding:10px; border-radius:4px;")
            scroll_layout.addWidget(sistemas_label)
            scroll_layout.addSpacing(15)

            # Nota para EXPRESSO
            try:
                if 'EXPRESSO' in item.sistemas_solicitados.upper() and item.status in ('Resolvido', 'Finalizado'):
                    note = QLabel("<i>Para solicitações do EXPRESSO a senha provisória será enviada para o email fornecido.</i>")
                    note.setStyleSheet("color: #555; font-style: italic;")
                    scroll_layout.addWidget(note)
                    scroll_layout.addSpacing(15)
            except Exception:
                pass

            # Credenciais, filtrando EXPRESSO
            if hasattr(item, 'credenciais_criadas') and item.credenciais_criadas:
                scroll_layout.addWidget(QLabel("<b>Credenciais Criadas:</b>"))
                
                cred_scroll = QScrollArea()
                cred_scroll.setWidgetResizable(True)
                cred_scroll.setStyleSheet("background-color:#e8f4f8; border: 1px solid #add8e6;")
                
                cred_widget = QWidget()
                cred_widget.setStyleSheet("background-color:#e8f4f8;")
                cred_layout = QVBoxLayout(cred_widget)
                cred_layout.setSpacing(10)

                try:
                    credenciais_data = json.loads(item.credenciais_criadas)
                    for sistema, cred in credenciais_data.items():
                        if sistema.strip().upper() == 'EXPRESSO':
                            continue
                        if '|' in cred:
                            login, senha = cred.split('|', 1)
                        else:
                            login, senha = cred, "***"
                        
                        system_frame = QWidget()
                        system_frame.setStyleSheet("background-color: white; border: 1px solid #add8e6; border-radius: 4px; padding: 10px;")
                        system_layout = QVBoxLayout(system_frame)
                        system_layout.setSpacing(3)
                        system_layout.setContentsMargins(10, 10, 10, 10)
                        
                        title = QLabel(f"<b>{sistema}</b>")
                        system_layout.addWidget(title)
                        
                        login_label = QLabel(f"<b>Login:</b> <span style='font-family: monospace; background-color: #f9f9f9; padding: 2px 5px;'>{login}</span>")
                        login_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
                        system_layout.addWidget(login_label)
                        
                        senha_label = QLabel(f"<b>Senha:</b> <span style='font-family: monospace; background-color: #f9f9f9; padding: 2px 5px;'>{senha}</span>")
                        senha_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
                        system_layout.addWidget(senha_label)
                        
                        cred_layout.addWidget(system_frame)
                except (json.JSONDecodeError, TypeError):
                    cred_label = QLabel(item.credenciais_criadas)
                    cred_label.setWordWrap(True)
                    cred_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
                    cred_layout.addWidget(cred_label)
                
                cred_layout.addStretch()
                cred_scroll.setWidget(cred_widget)
                scroll_layout.addWidget(cred_scroll)
            
            scroll_layout.addStretch()
            scroll.setWidget(scroll_content)
            layout.addWidget(scroll)
            
            # Botão para confirmar
            btn_confirm = QPushButton("Confirmar Atendimento")
            btn_confirm.setObjectName("SubmitBtn")
            btn_confirm.setMinimumHeight(40)
            btn_confirm.setMinimumWidth(200)
            btn_confirm.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 10px;
                    font-size: 14px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
                QPushButton:pressed {
                    background-color: #3e8e41;
                }
            """)
            btn_confirm.clicked.connect(lambda: self.confirmar_fechamento(solicitacao_id, 'solicitacao', dialog))
            layout.addWidget(btn_confirm)
            
            dialog.exec()
        except Exception as e:
            QMessageBox.warning(self, "Erro", f"Erro ao abrir confirmação: {str(e)}")

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