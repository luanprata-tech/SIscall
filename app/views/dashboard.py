import os
import sys
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QLabel, QTableWidget, 
    QTableWidgetItem, QHeaderView, QAbstractItemView, QStyledItemDelegate,
    QFrame, QGridLayout
)
from PySide6.QtCore import Qt, QTimer, QUrl
from PySide6.QtGui import QColor, QFont, QBrush
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from datetime import datetime

class HighlightDelegate(QStyledItemDelegate):
    """
    Este delegate customiza a pintura das células. Ele é usado para
    garantir que o destaque de cor funcione de forma confiável,
    sobrepondo-se a qualquer folha de estilo (stylesheet) aplicada.
    """
    def paint(self, painter, option, index):
        # Verifica um dado customizado (UserRole) que definimos no item.
        # Se o dado for True, significa que a célula deve ser destacada.
        if index.data(Qt.UserRole):
            # Altera a cor de fundo da opção de pintura para a cor de destaque.
            option.backgroundBrush = QBrush(QColor("#e67e22")) # Laranja

        # Chama o método 'paint' da classe base para desenhar a célula
        # com a opção (possivelmente) modificada.
        super().paint(painter, option, index)

class DashboardWindow(QMainWindow):
    def __init__(self, chamado_controller):
        super().__init__()
        self.controller = chamado_controller
        self.setWindowTitle("Dashboard de Chamados Abertos")
        self.setMinimumSize(1280, 720)
        self.setStyleSheet("background-color: #2c3e50;") # Tema escuro para a TV

        self.known_ticket_ids = set()
        self._first_run = True

        self.setup_ui()
        self.setup_sound()

        # Timer para atualizar os dados a cada 1 segundo (para efeito de piscar)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_data)
        self.timer.start(1000)
        self.refresh_data()

    def setup_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)

        header = QLabel("Chamados em Aberto")
        header.setStyleSheet("font-size: 32px; font-weight: bold; color: white; margin: 20px;")
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)

        # --- PAINEL DE DESTAQUE PARA O ÚLTIMO CHAMADO ---
        self.latest_ticket_frame = QFrame()
        self.latest_ticket_frame.setObjectName("LatestTicketFrame")
        self.latest_ticket_frame.setStyleSheet("""
            #LatestTicketFrame {
                background-color: #458BD2; /* Azul do tema, igual ao cabeçalho da tabela */
                border-radius: 8px;
                padding: 15px;
                margin: 0 20px 10px 20px;
            }
            #LatestTicketFrame QLabel {
                color: white;
                background-color: transparent;
                font-size: 20px;
            }
            #LatestTicketFrame QLabel#LatestDesc {
                font-size: 24px;
                font-weight: bold;
                padding-top: 5px;
            }
        """)
        latest_layout = QGridLayout(self.latest_ticket_frame)
        latest_layout.setSpacing(10)

        # Título do painel de destaque
        lbl_title = QLabel("ÚLTIMO CHAMADO")
        lbl_title.setStyleSheet("font-size: 16px; font-weight: bold; color: white; border-bottom: 1px solid rgba(255, 255, 255, 0.5); padding-bottom: 5px; margin-bottom: 5px;")
        lbl_title.setAlignment(Qt.AlignCenter)
        latest_layout.addWidget(lbl_title, 0, 0, 1, 4)

        self.lbl_latest_setor = QLabel("-")
        self.lbl_latest_usuario = QLabel("-")
        self.lbl_latest_maquina = QLabel("-")
        self.lbl_latest_horario = QLabel("-")
        self.lbl_latest_descricao = QLabel("...")
        self.lbl_latest_descricao.setObjectName("LatestDesc")
        self.lbl_latest_descricao.setWordWrap(True)

        latest_layout.addWidget(QLabel("<b>Setor:</b>"), 1, 0)
        latest_layout.addWidget(self.lbl_latest_setor, 1, 1)
        latest_layout.addWidget(QLabel("<b>Usuário:</b>"), 1, 2)
        latest_layout.addWidget(self.lbl_latest_usuario, 1, 3)
        latest_layout.addWidget(QLabel("<b>Máquina:</b>"), 2, 0)
        latest_layout.addWidget(self.lbl_latest_maquina, 2, 1)
        latest_layout.addWidget(QLabel("<b>Horário:</b>"), 2, 2)
        latest_layout.addWidget(self.lbl_latest_horario, 2, 3)
        latest_layout.addWidget(self.lbl_latest_descricao, 3, 0, 1, 4)

        latest_layout.setColumnStretch(1, 1)
        latest_layout.setColumnStretch(3, 1)
        self.latest_ticket_frame.setVisible(False)
        layout.addWidget(self.latest_ticket_frame)

        self.table = QTableWidget()
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #34495e;
                color: white;
                gridline-color: #2c3e50;
                font-size: 16px;
                border: none;
            }
            QTableWidget::item {
                padding: 15px;
                border-bottom: 1px solid #4a627a;
            }
            QHeaderView::section {
                background-color: #458BD2;
                color: white;
                padding: 15px;
                border: none;
                font-weight: bold;
                font-size: 18px;
            }
        """)
        self.table.setAlternatingRowColors(False)
        cols = ["Setor", "Usuário", "Máquina", "Hora", "Data", "Descrição", "Status"]
        self.table.setColumnCount(len(cols))
        self.table.setHorizontalHeaderLabels(cols)

        self.table.setColumnWidth(0, 200)
        self.table.setColumnWidth(1, 200)
        self.table.setColumnWidth(2, 150)
        self.table.setColumnWidth(3, 100)
        self.table.setColumnWidth(4, 120)
        self.table.setColumnWidth(6, 150)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch)

        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(80) # Linhas mais altas
        self.table.setWordWrap(True)

        # Aplica o delegate customizado para garantir que o destaque funcione
        self.table.setItemDelegate(HighlightDelegate(self.table))

        layout.addWidget(self.table)

    def setup_sound(self):
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        
        # Constrói o caminho para a pasta 'assets' na raiz do projeto
        sound_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'assets', 'notification.wav')) # Usando .wav
        if os.path.exists(sound_path):
            self.player.setSource(QUrl.fromLocalFile(sound_path))
            self.audio_output.setVolume(1.0)
        else:
            print(f"AVISO: Arquivo de som 'notification.wav' não encontrado em '{sound_path}'")

    def refresh_data(self):
        try:
            chamados = self.controller.listar_pendentes()
            current_ticket_ids = {c.id for c in chamados}

            # Verifica se há novos chamados desde a última atualização
            new_tickets = current_ticket_ids - self.known_ticket_ids
            if not self._first_run and new_tickets:
                if self.player.playbackState() == QMediaPlayer.PlayingState:
                    self.player.stop()
                self.player.play()

            self._first_run = False
            self.known_ticket_ids = current_ticket_ids

            if chamados:
                # O primeiro da lista é o mais recente
                latest_ticket = chamados[0]
                # O resto vai para a tabela
                other_tickets = chamados[1:]
                
                self.update_latest_ticket_display(latest_ticket)
                self.latest_ticket_frame.setVisible(True)
                self.preencher_tabela(other_tickets)
            else:
                # Se não houver chamados, esconde o painel e limpa a tabela
                self.latest_ticket_frame.setVisible(False)
                self.preencher_tabela([])

        except Exception as e:
            print(f"Erro ao atualizar dashboard: {e}")

    def update_latest_ticket_display(self, ticket):
        dt_obj = datetime.strptime(ticket.data_abertura, "%Y-%m-%d %H:%M:%S") if ticket.data_abertura else None
        self.lbl_latest_setor.setText(ticket.setor_usuario)
        self.lbl_latest_usuario.setText(ticket.nome_usuario)
        self.lbl_latest_maquina.setText(ticket.maquina or "N/A")
        self.lbl_latest_horario.setText(dt_obj.strftime('%H:%M - %d/%m/%Y') if dt_obj else "")
        self.lbl_latest_descricao.setText(ticket.descricao)

    def preencher_tabela(self, chamados):
        self.table.setRowCount(len(chamados))
        def parse_date(date_str):
            try:
                # Simplesmente converte a string para um objeto datetime "naive" (sem fuso).
                return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
            except (ValueError, TypeError):
                return None
        
        # Pega a hora atual "naive" do PC, que é a mesma base do banco de dados.
        agora = datetime.now()
        
        for i, c in enumerate(chamados):
            # dt_obj é um objeto datetime "naive" (sem fuso)
            dt_obj = parse_date(c.data_abertura)

            is_highlighted = False
            if dt_obj:
                # A diferença entre dois datetimes "naive" (do mesmo fuso) é um timedelta.
                diff_seconds = (agora - dt_obj).total_seconds()
                
                # Garante que a diferença é positiva e dentro do nosso limite.
                if 0 <= diff_seconds < 20:
                    # Ciclo de 1 segundo aceso, 1 segundo apagado
                    if int(diff_seconds) % 2 == 0:
                        is_highlighted = True
            
            items = [
                QTableWidgetItem(c.setor_usuario),
                QTableWidgetItem(c.nome_usuario),
                QTableWidgetItem(c.maquina or "N/A"),
                QTableWidgetItem(dt_obj.strftime('%H:%M') if dt_obj else ""),
                QTableWidgetItem(dt_obj.strftime('%d/%m/%y') if dt_obj else ""),
                QTableWidgetItem(c.descricao),
                QTableWidgetItem(c.status)
            ]

            status_item = items[-1]
            status_item.setFont(QFont("Segoe UI", 16, QFont.Bold))
            status_color = {"Aberto": "#e74c3c", "Em andamento": "#3498db", "Resolvido": "#f1c40f"}.get(c.status, "#ecf0f1")
            status_item.setForeground(QColor(status_color))

            for col, item in enumerate(items):
                item.setTextAlignment(Qt.AlignCenter)
                if col == 5: item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                
                item.setData(Qt.UserRole, is_highlighted)
                
                self.table.setItem(i, col, item)
