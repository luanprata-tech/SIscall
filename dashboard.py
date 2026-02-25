import sys
import os
import traceback

# Define variável de ambiente para compatibilidade com Linux
if sys.platform == "linux":
    os.environ["QT_QPA_PLATFORM"] = "xcb"

try:
    from PySide6.QtWidgets import QApplication
    from app.core.database import DatabaseManager
    from app.repositories import ChamadoRepository
    from app.controllers import ChamadoController
    from app.views import DashboardWindow, STYLESHEET
except ImportError as e:
    print(f"ERRO DE IMPORTAÇÃO: {e}")
    sys.exit(1)

class DashboardApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        # Usamos o mesmo estilo base, mas a janela do dashboard terá seu próprio tema escuro
        self.app.setStyleSheet(STYLESHEET)

        # Configura o acesso ao banco de dados e aos controllers
        try:
            self.db_manager = DatabaseManager()
            self.db_manager.setup()
            session_factory = self.db_manager.get_session
            chamado_repo = ChamadoRepository(session_factory)
            self.chamado_controller = ChamadoController(chamado_repo)
        except Exception as e:
            print(f"ERRO AO CONECTAR AO BANCO: {e}")
            sys.exit(1)

        # Cria e exibe a janela do dashboard
        self.window = DashboardWindow(self.chamado_controller)
        self.window.show()

    def run(self):
        return self.app.exec()

if __name__ == "__main__":
    try:
        dashboard = DashboardApp()
        sys.exit(dashboard.run())
    except Exception as e:
        print(f"\n!!! OCORREU UM ERRO FATAL NO DASHBOARD !!!\nERRO: {e}")
        traceback.print_exc()
