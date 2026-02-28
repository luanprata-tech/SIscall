import os
import sys
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView
)
from PySide6.QtCore import Qt, QTimer, QUrl
from PySide6.QtGui import QColor, QFont
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from datetime import datetime

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

        # Timer para atualizar os dados a cada 5 segundos
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_data)
        self.timer.start(5000)
        self.refresh_data()

    def setup_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)

        header = QLabel("Chamados em Aberto")
        header.setStyleSheet("font-size: 32px; font-weight: bold; color: white; margin: 20px;")
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)

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
            self.preencher_tabela(chamados)
        except Exception as e:
            print(f"Erro ao atualizar dashboard: {e}")

    def preencher_tabela(self, chamados):
        self.table.setRowCount(len(chamados))
        def parse_date(date_str):
            try: return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
            except: return None
        
        agora = datetime.now()
        for i, c in enumerate(chamados):
            dt_obj = parse_date(c.data_abertura)
            is_new = dt_obj and (agora - dt_obj).total_seconds() < 15

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
            status_item.setFont(QFont("Segoe UI", 10, QFont.Bold))
            status_color = {"Aberto": "#e74c3c", "Em andamento": "#3498db", "Resolvido": "#f1c40f"}.get(c.status, "#ecf0f1")
            status_item.setForeground(QColor(status_color))

            for col, item in enumerate(items):
                item.setTextAlignment(Qt.AlignCenter)
                if col == 5: item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                
                # Aplica o destaque de cor para novos chamados
                if is_new:
                    item.setBackground(QColor("#e67e22")) # Laranja
                
                self.table.setItem(i, col, item)
