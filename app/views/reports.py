from datetime import datetime, timedelta

from PySide6.QtCore import QMargins, Qt
from PySide6.QtGui import QColor, QPainter
from PySide6.QtPrintSupport import QPrinter
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QGraphicsDropShadowEffect,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

try:
    from PySide6.QtCharts import (
        QBarCategoryAxis,
        QBarSeries,
        QBarSet,
        QChart,
        QChartView,
        QLineSeries,
        QPieSeries,
        QValueAxis,
    )

    HAS_QT_CHARTS = True
except Exception:
    HAS_QT_CHARTS = False


ACCENT = "#2c3e50"
ACCENT_BLUE = "#2f80ed"
TEXT_DARK = "#1f2937"
TEXT_MUTED = "#6b7280"
CARD_BORDER = "#d8e1ea"
CARD_BG = "#ffffff"
PAGE_BG = "#f4f7fb"
PANEL_HEIGHT = 240
PANEL_CONTENT_HEIGHT = 190


class ReportCard(QFrame):
    def __init__(self):
        super().__init__()
        self.setObjectName("ReportCard")
        self.setFixedHeight(58)
        self._set_normal_style()

        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setColor(QColor(17, 24, 39, 35))
        self.shadow.setBlurRadius(12)
        self.shadow.setOffset(0, 3)
        self.setGraphicsEffect(self.shadow)

    def _set_normal_style(self):
        self.setStyleSheet(
            f"""
            QFrame#ReportCard {{
                background: {CARD_BG};
                border: 1px solid {CARD_BORDER};
                border-radius: 12px;
            }}
            """
        )

    def _set_hover_style(self):
        self.setStyleSheet(
            f"""
            QFrame#ReportCard {{
                background: #ffffff;
                border: 1px solid {ACCENT_BLUE};
                border-radius: 12px;
            }}
            """
        )

    def enterEvent(self, event):
        self._set_hover_style()
        self.shadow.setColor(QColor(47, 128, 237, 110))
        self.shadow.setBlurRadius(30)
        self.shadow.setOffset(0, 9)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._set_normal_style()
        self.shadow.setColor(QColor(17, 24, 39, 35))
        self.shadow.setBlurRadius(12)
        self.shadow.setOffset(0, 3)
        super().leaveEvent(event)


class PanelFrame(QFrame):
    def __init__(self):
        super().__init__()
        self.setObjectName("PanelFrame")
        self.setStyleSheet(
            f"""
            QFrame#PanelFrame {{
                background: {CARD_BG};
                border: 1px solid {CARD_BORDER};
                border-radius: 12px;
            }}
            """
        )


def export_widget_to_pdf(parent, widget):
    """Exporta o conteúdo do widget para um arquivo PDF selecionado pelo usuário."""
    try:
        filename, _ = QFileDialog.getSaveFileName(parent, "Salvar PDF", "relatorios.pdf", "PDF Files (*.pdf)")
        if not filename:
            return

        if not filename.lower().endswith(".pdf"):
            filename += ".pdf"

        printer = QPrinter()
        printer.setOutputFormat(QPrinter.PdfFormat)
        printer.setOutputFileName(filename)

        painter = QPainter()
        if not painter.begin(printer):
            QMessageBox.warning(parent, "Erro", "Não foi possível iniciar a exportação para PDF.")
            return

        widget.render(painter)
        painter.end()

        QMessageBox.information(parent, "Exportado", f"Relatórios exportados para:\n{filename}")
    except Exception as e:
        QMessageBox.warning(parent, "Erro", f"Falha ao exportar PDF: {e}")


def _parse_date_text(value: str):
    if not value or value.strip("/ ") == "":
        return None
    return datetime.strptime(value, "%d/%m/%Y")


def _format_duration(seconds: float) -> str:
    if seconds is None or seconds < 0:
        return "N/A"
    total_minutes = int(seconds // 60)
    hours = total_minutes // 60
    minutes = total_minutes % 60
    return f"{hours}h {minutes}m"


def _build_card(title: str, value: str) -> QFrame:
    card = ReportCard()
    card_layout = QVBoxLayout(card)
    card_layout.setContentsMargins(12, 8, 12, 8)
    card_layout.setSpacing(2)

    title_label = QLabel(title)
    title_label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 10px; font-weight: 600; text-transform: uppercase;")
    value_label = QLabel(value)
    value_label.setObjectName("ReportValue")
    value_label.setStyleSheet(f"color: {TEXT_DARK}; font-size: 18px; font-weight: 800;")
    

    card_layout.addWidget(title_label)
    card_layout.addWidget(value_label)
    

    card.value_label = value_label
    return card


class ReportsPage(QWidget):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.parent_window = parent
        self.controller = controller
        self.setObjectName("ReportsPage")
        self._build_ui()
        self.refresh_reports()

    def _build_ui(self):
        self.setStyleSheet(f"background: {PAGE_BG};")

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(20, 20, 20, 20)
        root_layout.setSpacing(16)

        top_row = QHBoxLayout()
        title = QLabel("Relatórios")
        title.setStyleSheet(f"color: {TEXT_DARK}; font-size: 26px; font-weight: 800;")

        self.btn_export = QPushButton("Exportar PDF")
        self.btn_export.setFixedSize(140, 36)
        self.btn_export.setStyleSheet(
            f"""
            QPushButton {{
                background: transparent;
                color: {ACCENT_BLUE};
                border: 2px solid {ACCENT_BLUE};
                border-radius: 8px;
                padding: 6px 12px;
                font-weight: 700;
            }}
            QPushButton:hover {{
                background: {ACCENT_BLUE};
                color: white;
            }}
            """
        )
        self.btn_export.clicked.connect(lambda: export_widget_to_pdf(self, self))

        top_row.addWidget(title)
        top_row.addStretch()
        top_row.addWidget(self.btn_export)
        root_layout.addLayout(top_row)

        period_frame = QFrame()
        period_frame.setStyleSheet(
            f"""
            QFrame {{
                background: transparent;
            }}
            QLineEdit {{
                background: white;
                color: {TEXT_DARK};
                border: 1px solid {CARD_BORDER};
                border-radius: 8px;
                padding: 7px 10px;
                font-size: 13px;
            }}
            QLineEdit:focus {{
                border: 1px solid {ACCENT_BLUE};
            }}
            QLabel {{
                color: {TEXT_MUTED};
                font-size: 13px;
            }}
            """
        )
        period_layout = QHBoxLayout(period_frame)
        period_layout.setContentsMargins(0, 0, 0, 0)
        period_layout.setSpacing(8)

        self.txt_date_inicio = QLineEdit()
        self.txt_date_inicio.setInputMask("00/00/0000")
        self.txt_date_inicio.setFixedWidth(110)
        self.txt_date_inicio.setPlaceholderText("dd/mm/aaaa")

        self.txt_date_fim = QLineEdit()
        self.txt_date_fim.setInputMask("00/00/0000")
        self.txt_date_fim.setFixedWidth(110)
        self.txt_date_fim.setPlaceholderText("dd/mm/aaaa")

        hoje = datetime.today()
        self.txt_date_inicio.setText((hoje - timedelta(days=30)).strftime("%d/%m/%Y"))
        self.txt_date_fim.setText(hoje.strftime("%d/%m/%Y"))

        self.btn_gerar = QPushButton("Gerar")
        self.btn_gerar.setFixedSize(90, 34)
        self.btn_gerar.setStyleSheet(
            f"""
            QPushButton {{
                background: {ACCENT};
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: 700;
            }}
            QPushButton:hover {{
                background: {ACCENT_BLUE};
            }}
            """
        )
        self.btn_gerar.clicked.connect(self.refresh_reports)

        self.txt_date_inicio.returnPressed.connect(self.refresh_reports)
        self.txt_date_fim.returnPressed.connect(self.refresh_reports)

        period_layout.addStretch()
        period_layout.addWidget(QLabel("De"))
        period_layout.addWidget(self.txt_date_inicio)
        period_layout.addWidget(QLabel("até"))
        period_layout.addWidget(self.txt_date_fim)
        period_layout.addWidget(self.btn_gerar)
        root_layout.addWidget(period_frame)

        # Scroll area para os gráficos
        scroll = QScrollArea()
        scroll.setStyleSheet(f"background: {PAGE_BG}; border: none;")
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        # Container para os gráficos
        scroll_widget = QWidget()
        scroll_widget.setStyleSheet(f"background: {PAGE_BG};")
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(16)

        # 1a linha: cards KPI
        cards_frame = QFrame()
        cards_frame.setStyleSheet("background: transparent;")
        cards_grid = QGridLayout(cards_frame)
        cards_grid.setContentsMargins(0, 0, 0, 0)
        cards_grid.setHorizontalSpacing(10)
        cards_grid.setVerticalSpacing(10)

        self.card_total = _build_card("Total no período", "0")
        self.card_abertos_fechados = _build_card("Abertos vs fechados", "0 / 0")
        self.card_tempo_atendimento = _build_card("Tempo médio de atendimento", "N/A")
        self.card_mais_1_dia = _build_card("Acima de 1 dia", "0")

        cards_grid.setColumnStretch(0, 1)
        cards_grid.setColumnStretch(1, 1)
        cards_grid.setColumnStretch(2, 1)
        cards_grid.setColumnStretch(3, 1)

        cards_grid.addWidget(self.card_total, 0, 0)
        cards_grid.addWidget(self.card_abertos_fechados, 0, 1)
        cards_grid.addWidget(self.card_tempo_atendimento, 0, 2)
        cards_grid.addWidget(self.card_mais_1_dia, 0, 3)
        scroll_layout.addWidget(cards_frame)

        # 2a linha: segmentação/categorização
        segment_frame = QFrame()
        segment_grid = QGridLayout(segment_frame)
        segment_grid.setContentsMargins(0, 0, 0, 0)
        segment_grid.setHorizontalSpacing(10)
        segment_grid.setVerticalSpacing(10)

        self.panel_status, self.layout_status = self._build_panel("Por Status")
        self.panel_department, self.layout_department = self._build_panel("Top 3 Setores com mais chamados")

        segment_grid.addWidget(self.panel_status, 0, 0)
        segment_grid.addWidget(self.panel_department, 0, 1)

        segment_grid.setColumnStretch(0, 1)
        segment_grid.setColumnStretch(1, 1)
        scroll_layout.addWidget(segment_frame)

        # 3a linha: tendência e pico
        trend_frame = QFrame()
        trend_grid = QGridLayout(trend_frame)
        trend_grid.setContentsMargins(0, 0, 0, 0)
        trend_grid.setHorizontalSpacing(10)

        self.panel_timeline, self.layout_timeline = self._build_panel("Volume Mensal")
        self.panel_peak_hours, self.layout_peak_hours = self._build_panel("Horários de Pico")

        trend_grid.addWidget(self.panel_timeline, 0, 0)
        trend_grid.addWidget(self.panel_peak_hours, 0, 1)
        trend_grid.setColumnStretch(0, 2)
        trend_grid.setColumnStretch(1, 2)
        scroll_layout.addWidget(trend_frame)

        # 4a linha: semanal e suportes
        support_frame = QFrame()
        support_grid = QGridLayout(support_frame)
        support_grid.setContentsMargins(0, 0, 0, 0)
        support_grid.setHorizontalSpacing(10)
        support_grid.setVerticalSpacing(10)

        self.panel_weekday, self.layout_weekday = self._build_panel("Chamados por Dia da Semana")
        self.panel_suportes, self.layout_suportes = self._build_panel("Top 3 Suportes")

        support_grid.addWidget(self.panel_weekday, 0, 0)
        support_grid.addWidget(self.panel_suportes, 0, 1)

        support_grid.setColumnStretch(0, 1)
        support_grid.setColumnStretch(1, 1)
        scroll_layout.addWidget(support_frame)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_widget)
        root_layout.addWidget(scroll)

        # Estado inicial dos gráficos
        self._fill_empty_panels()

    def _build_panel(self, title: str):
        frame = PanelFrame()
        frame.setFixedHeight(PANEL_HEIGHT)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(8)

        title_label = QLabel(title)
        title_label.setStyleSheet(f"color: {TEXT_DARK}; font-size: 12px; font-weight: 700;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        content = QVBoxLayout()
        content.setContentsMargins(0, 0, 0, 0)
        content.setSpacing(0)
        layout.addLayout(content)
        return frame, content

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

    def _set_panel_widget(self, layout, widget):
        self._clear_layout(layout)
        layout.addWidget(widget)

    def _build_info_label(self, text: str):
        lbl = QLabel(text)
        lbl.setWordWrap(True)
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setFixedHeight(PANEL_CONTENT_HEIGHT)
        lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px; padding: 8px;")
        return lbl

    def _build_pie_chart(self, data_map, max_items=6):
        if not HAS_QT_CHARTS:
            return self._build_info_label("QtCharts indisponível no ambiente")

        filtered = [(k, int(v)) for k, v in data_map.items() if int(v) > 0]
        filtered = sorted(filtered, key=lambda x: x[1], reverse=True)[:max_items]
        if not filtered:
            return self._build_info_label("Sem dados no período")

        series = QPieSeries()
        palette = ["#2f80ed", "#27ae60", "#f2994a", "#eb5757", "#9b51e0", "#56ccf2"]
        for idx, (label, value) in enumerate(filtered):
            sl = series.append(f"{label} ({value})", value)
            sl.setColor(QColor(palette[idx % len(palette)]))

        chart = QChart()
        chart.addSeries(series)
        chart.legend().setVisible(True)
        chart.legend().setLabelColor(QColor(TEXT_DARK))
        chart.setBackgroundVisible(False)
        chart.setMargins(QMargins(0, 0, 0, 0))

        view = QChartView(chart)
        view.setFixedHeight(PANEL_CONTENT_HEIGHT)
        view.setRenderHint(QPainter.Antialiasing)
        view.setStyleSheet("background: transparent;")
        return view

    def _build_bar_chart(self, data_map, max_items=8):
        if not HAS_QT_CHARTS:
            return self._build_info_label("QtCharts indisponível no ambiente")

        filtered = [(k, int(v)) for k, v in data_map.items() if int(v) > 0]
        filtered = sorted(filtered, key=lambda x: x[1], reverse=True)[:max_items]
        if not filtered:
            return self._build_info_label("Sem dados no período")

        categories = [k for k, _ in filtered]
        values = [v for _, v in filtered]

        bar_set = QBarSet("Total")
        bar_set.setColor(QColor(ACCENT_BLUE))
        for value in values:
            bar_set.append(value)

        series = QBarSeries()
        series.append(bar_set)

        chart = QChart()
        chart.addSeries(series)
        chart.legend().setVisible(False)
        chart.setBackgroundVisible(False)
        chart.setMargins(QMargins(0, 0, 0, 0))

        axis_x = QBarCategoryAxis()
        axis_x.append(categories)
        axis_x.setLabelsColor(QColor(TEXT_MUTED))
        axis_y = QValueAxis()
        axis_y.setLabelFormat("%d")
        axis_y.setLabelsColor(QColor(TEXT_MUTED))

        chart.addAxis(axis_x, Qt.AlignBottom)
        chart.addAxis(axis_y, Qt.AlignLeft)
        series.attachAxis(axis_x)
        series.attachAxis(axis_y)

        view = QChartView(chart)
        view.setFixedHeight(PANEL_CONTENT_HEIGHT)
        view.setRenderHint(QPainter.Antialiasing)
        view.setStyleSheet("background: transparent;")
        return view

    def _build_monthly_bar_chart(self, labels, created):
        if not HAS_QT_CHARTS:
            return self._build_info_label("QtCharts indisponível no ambiente")

        if not labels:
            return self._build_info_label("Sem dados no período")

        created_set = QBarSet("Criados")
        created_set.setColor(QColor("#2f80ed"))

        max_y = 0
        for value in created:
            v = int(value)
            created_set.append(v)
            max_y = max(max_y, v)

        series = QBarSeries()
        series.append(created_set)

        chart = QChart()
        chart.addSeries(series)
        chart.legend().setVisible(True)
        chart.legend().setLabelColor(QColor(TEXT_DARK))
        chart.setBackgroundVisible(False)
        chart.setMargins(QMargins(0, 0, 0, 0))

        axis_x = QBarCategoryAxis()
        axis_x.append(labels)
        axis_x.setLabelsColor(QColor(TEXT_MUTED))

        axis_y = QValueAxis()
        axis_y.setRange(0, max(1, max_y + 1))
        axis_y.setLabelFormat("%d")
        axis_y.setLabelsColor(QColor(TEXT_MUTED))

        chart.addAxis(axis_x, Qt.AlignBottom)
        chart.addAxis(axis_y, Qt.AlignLeft)
        series.attachAxis(axis_x)
        series.attachAxis(axis_y)

        view = QChartView(chart)
        view.setFixedHeight(PANEL_CONTENT_HEIGHT)
        view.setRenderHint(QPainter.Antialiasing)
        view.setStyleSheet("background: transparent;")
        return view

    def _build_peak_hours_chart(self, matrix_7x24):
        if not HAS_QT_CHARTS:
            return self._build_info_label("QtCharts indisponível no ambiente")

        hours = list(range(7, 14))
        values = []
        for hour in hours:
            total = 0
            for day in range(7):
                total += int(matrix_7x24[day][hour])
            values.append(total)

        if sum(values) == 0:
            return self._build_info_label("Sem dados entre 07h e 13h no período")

        series = QLineSeries()
        series.setName("Chamados")
        series.setColor(QColor("#eb5757"))
        max_y = 0
        for i, value in enumerate(values):
            series.append(i, value)
            max_y = max(max_y, value)

        chart = QChart()
        chart.addSeries(series)
        chart.legend().setVisible(False)
        chart.setBackgroundVisible(False)
        chart.setMargins(QMargins(0, 0, 0, 0))

        axis_x = QBarCategoryAxis()
        axis_x.append([f"{h:02d}h" for h in hours])
        axis_x.setLabelsColor(QColor(TEXT_MUTED))

        axis_y = QValueAxis()
        axis_y.setRange(0, max(1, max_y + 1))
        axis_y.setLabelFormat("%d")
        axis_y.setLabelsColor(QColor(TEXT_MUTED))

        chart.addAxis(axis_x, Qt.AlignBottom)
        chart.addAxis(axis_y, Qt.AlignLeft)
        series.attachAxis(axis_x)
        series.attachAxis(axis_y)

        view = QChartView(chart)
        view.setFixedHeight(PANEL_CONTENT_HEIGHT)
        view.setRenderHint(QPainter.Antialiasing)
        view.setStyleSheet("background: transparent;")
        return view

    def _fill_empty_panels(self):
        empty = self._build_info_label("Selecione um período e clique em Gerar")
        self._set_panel_widget(self.layout_status, self._build_info_label(empty.text()))
        self._set_panel_widget(self.layout_department, self._build_info_label(empty.text()))
        self._set_panel_widget(self.layout_timeline, self._build_info_label(empty.text()))
        self._set_panel_widget(self.layout_peak_hours, self._build_info_label(empty.text()))
        self._set_panel_widget(self.layout_weekday, self._build_info_label(empty.text()))
        self._set_panel_widget(self.layout_suportes, self._build_info_label(empty.text()))

    def _set_card(self, card: QFrame, value: str):
        card.value_label.setText(str(value))
        

    def _read_period(self):
        try:
            data_inicio = _parse_date_text(self.txt_date_inicio.text().strip())
            data_fim = _parse_date_text(self.txt_date_fim.text().strip())
        except Exception:
            QMessageBox.warning(self, "Data inválida", "Digite as datas no formato dd/mm/aaaa")
            return None

        if not data_inicio or not data_fim:
            QMessageBox.warning(self, "Data inválida", "Preencha as duas datas no formato dd/mm/aaaa")
            return None

        if data_inicio > data_fim:
            QMessageBox.warning(self, "Data inválida", "A data inicial não pode ser maior que a final")
            return None

        return data_inicio, data_fim

    def refresh_reports(self):
        period = self._read_period()
        if not period:
            return

        data_inicio, data_fim = period
        try:
            data = self.controller.gerar_relatorio(
                data_inicio.strftime("%Y-%m-%d"),
                data_fim.strftime("%Y-%m-%d"),
            )
        except Exception as e:
            QMessageBox.warning(self, "Erro", f"Falha ao gerar relatórios: {e}")
            return

        total_periodo = data.get("total_periodo", 0)
        abertos = data.get("abertos", 0)
        fechados = data.get("fechados", 0)
        tempo_medio_atendimento = data.get("tempo_medio_atendimento", "N/A")
        acima_1_dia = data.get("mais_1_dia", 0)

        self._set_card(self.card_total, total_periodo)
        self._set_card(self.card_abertos_fechados, f"{abertos} / {fechados}")
        self._set_card(self.card_tempo_atendimento, tempo_medio_atendimento)
        self._set_card(self.card_mais_1_dia, acima_1_dia)

        status_counts = data.get("status_counts", {})
        department_counts = data.get("department_counts", {})
        weekday_counts = data.get("weekday_counts", {})
        top_3_suportes = data.get("top_3_suportes", [])

        timeline_labels = data.get("monthly_labels", [str(m) for m in range(1, 13)])
        timeline_created = data.get("monthly_created", [0] * 12)
        heatmap = data.get("heatmap_weekday_hour", [[0] * 24 for _ in range(7)])

        self._set_panel_widget(self.layout_status, self._build_pie_chart(status_counts))
        self._set_panel_widget(self.layout_department, self._build_bar_chart(department_counts, max_items=3))
        self._set_panel_widget(self.layout_timeline, self._build_monthly_bar_chart(timeline_labels, timeline_created))
        self._set_panel_widget(self.layout_peak_hours, self._build_peak_hours_chart(heatmap))
        self._set_panel_widget(self.layout_weekday, self._build_bar_chart(weekday_counts))
        
        suportes_dict = {nome: int(qtd) for nome, qtd in top_3_suportes} if top_3_suportes else {}
        self._set_panel_widget(self.layout_suportes, self._build_bar_chart(suportes_dict, max_items=3))
