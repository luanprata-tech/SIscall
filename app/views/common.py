# views/common.py
from PySide6.QtCore import QTimer
from PySide6.QtGui import QGuiApplication, QColor
from PySide6.QtWidgets import QGraphicsDropShadowEffect

# --- ESTILOS GLOBAIS ---
STYLESHEET = """
QMainWindow, QDialog { background-color: #f0f3f4; }
QWidget { font-family: 'Segoe UI', sans-serif; font-size: 14px; }
QLabel { color: #333333; }

/* Botões Padrão */
QPushButton { 
    background-color: #458BD2; color: white; border-radius: 4px; 
    padding: 8px 16px; font-weight: bold; border: none;
}
QPushButton:hover { background-color: #537DA7; }
QPushButton:disabled { background-color: #bdc3c7; color: #7f8c8d; }
QPushButton#Danger { background-color: #d32f2f; }
QPushButton#Info { background-color: #2196F3; } 
QPushButton#Secondary { background-color: #757575; }
QPushButton#Link { background-color: transparent; color: #537DA7; border: none; text-decoration: underline;}

/* Badge de contagem */
QLabel#CountBadge {
    background-color: #d32f2f;
    color: white;
    font-size: 11px;
    font-weight: bold;
    min-width: 20px;
    max-width: 20px;
    height: 20px;
    border-radius: 10px;
}

/* Botão de Submit (Verde Grande) */
QPushButton#SubmitBtn { 
    background-color: #458BD2; color: white; border: none;
    border-radius: 4px; font-size: 16px; padding: 12px; font-weight: bold;
}
QPushButton#SubmitBtn:hover { background-color: #537DA7; }

/* Menu Lateral */
QWidget#Sidebar { background-color: #2c3e50; min-width: 250px; max-width: 250px; }
QPushButton#MenuBtn { background-color: transparent; color: #ecf0f1; text-align: left; padding: 12px 20px; border: none; font-size: 15px; }
QPushButton#MenuBtn:hover { background-color: #34495e; border-left: 4px solid #4CAF50; }
QPushButton#MenuBtn:checked { background-color: #34495e; border-left: 4px solid #4CAF50; font-weight: bold; }
QLabel#MenuTitle { color: white; font-size: 20px; font-weight: bold; padding: 30px 10px; }

/* Estilo para o texto (QLabel) dentro de um botão de menu com badge */
QPushButton#MenuBtn QLabel {
    color: #ecf0f1; /* Cor branca padrão do menu */
    background-color: transparent;
    border: none;
    font-size: 15px; /* Garante o mesmo tamanho de fonte dos outros botões */
}
QPushButton#MenuBtn:checked QLabel {
    font-weight: bold; /* Deixa o texto em negrito quando o botão está selecionado */
}

/* Tabelas */
QTableWidget { 
    background-color: white; color: #333333; selection-background-color: #e3f2fd; selection-color: black; border: 1px solid #ddd;
    font-size: 14px; alternate-background-color: #fafafa;
}
QTableWidget::item { padding: 10px; border-bottom: 1px solid #f0f0f0; }
QHeaderView::section { background-color: #34495e; color: white; padding: 10px; border: none; font-weight: bold; font-size: 14px; }

/* Inputs */
QLineEdit, QPlainTextEdit, QComboBox, QDateEdit { 
    border: 1px solid #ccc; border-radius: 4px; padding: 8px; 
    background-color: white; color: #333333; 
}
QComboBox QAbstractItemView {
    background-color: white; color: #333333; selection-background-color: #4CAF50; selection-color: white;
    border: 1px solid #ccc; outline: none;
}

/* Checkbox Customizado */
QCheckBox {
    color: black;
}
QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border: 1px solid #ccc;
    border-radius: 4px;
    background-color: white;
}
QCheckBox::indicator:hover {
    border: 1px solid #458BD2;
}
QCheckBox::indicator:checked {
    background-color: #458BD2;
    border: 1px solid #458BD2;
    image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24"><path fill="white" d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/></svg>');
}

/* Cards de Relatório */
QGroupBox {
    background-color: white; border: 1px solid #ddd; border-radius: 8px; margin-top: 20px; font-weight: bold; color: #2c3e50;
}
QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }
QLabel#MetricValue { font-size: 24px; font-weight: bold; color: #2E7D32; }
QLabel#MetricLabel { font-size: 14px; color: #7f8c8d; }
"""

class CenterMixin:
    def force_center(self):
        screen = QGuiApplication.primaryScreen().availableGeometry()
        size = self.geometry()
        x = (screen.width() - size.width()) // 2
        y = (screen.height() - size.height()) // 2
        self.move(x, y)
        
    def showEvent(self, event):
        super().showEvent(event)
        if not getattr(self, '_centered', False):
            QTimer.singleShot(10, self.force_center)
            self._centered = True

# --- CONSTANTES COMPARTILHADAS ---
LISTA_SETORES = sorted([
    "AGEPLAN", "AGEQUALI", "ARRECADAÇÂO", "ASCOM", "AUDITORIO", "COMEL", 
    "CONSEGER", "COTRANSP", "CPI", "DIRAF", "DITEC", "FISCAIS", "GEAAD", 
    "GEATEC", "GECONF", "GEINFORM", "GEMETRO", "GEREMETRO", "GERH", 
    "GUARITA", "LABAGUA", "LABMICRO", "LABORG", "LABROMO", "LABSOLOS", 
    "LEI", "OUVIDORIA", "PRE-MEDIDOS", "PRESIDENCIA", "PROJUR", "PROTOCOLO"
])

# --- FUNÇÃO HELPER PARA APLICAR EFEITO DE RELEVO ---
def apply_table_shadow(table_widget):
    """Aplica efeito de sombra/relevo a uma QTableWidget."""
    shadow = QGraphicsDropShadowEffect()
    shadow.setColor(QColor(17, 24, 39, 35))
    shadow.setBlurRadius(12)
    shadow.setOffset(0, 3)
    table_widget.setGraphicsEffect(shadow)
    return table_widget