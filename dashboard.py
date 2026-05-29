import sys
import os
import traceback
 
# --- INÍCIO DA CORREÇÃO PARA PLUGINS DE MÍDIA ---
# Adicionado para resolver problema de plugins (como áudio) no Windows
# Define explicitamente o caminho dos plugins do Qt para o ambiente.
try:
    # O método preferencial e mais robusto
    from PySide6.QtCore import QLibraryInfo
    plugin_path = QLibraryInfo.path(QLibraryInfo.PluginsPath)
    os.environ['QT_PLUGIN_PATH'] = plugin_path
except ImportError:
    # Um método de fallback caso o de cima falhe
    try:
        import PySide6
        plugin_path = os.path.join(os.path.dirname(PySide6.__file__), "plugins")
        if os.path.isdir(plugin_path):
            os.environ['QT_PLUGIN_PATH'] = plugin_path
    except Exception as e:
        print(f"AVISO: Falha ao tentar configurar o QT_PLUGIN_PATH: {e}")
 
# Define variável de ambiente para evitar problemas de renderização em diferentes SOs
if sys.platform == "win32":
    os.environ["QT_QPA_PLATFORM"] = "windows"
elif sys.platform == "darwin":  # macOS
    os.environ["QT_QPA_PLATFORM"] = "cocoa"
elif sys.platform == "linux":
    os.environ["QT_QPA_PLATFORM"] = "xcb"

try:
    from PySide6.QtWidgets import QApplication
    from app.core.database import DatabaseManager
    from app.repositories import ChamadoRepository, SolicitacaoContaRepository, IPRepository
    from app.controllers import ChamadoController, SolicitacaoContaController
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
            solicitacao_repo = SolicitacaoContaRepository(session_factory)
            ip_repo = IPRepository(session_factory)
            self.chamado_controller = ChamadoController(chamado_repo, ip_repo)
            self.solicitacao_controller = SolicitacaoContaController(solicitacao_repo)
        except Exception as e:
            print(f"ERRO AO CONECTAR AO BANCO: {e}")
            sys.exit(1)

        # Cria e exibe a janela do dashboard
        self.window = DashboardWindow(self.chamado_controller, self.solicitacao_controller)
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
