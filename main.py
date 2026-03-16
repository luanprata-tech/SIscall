import sys
import traceback
import os

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
# --- FIM DA CORREÇÃO ---

if sys.platform == "win32":
    os.environ["QT_QPA_PLATFORM"] = "windows"
elif sys.platform == "darwin":  # macOS
    os.environ["QT_QPA_PLATFORM"] = "cocoa"
elif sys.platform == "linux":
    os.environ["QT_QPA_PLATFORM"] = "xcb"

print(">>> Importando módulos...", flush=True)
try:
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import QTimer  
    from PySide6.QtGui import QIcon
    from app.core.database import DatabaseManager
    from app.repositories import UsuarioRepository, ChamadoRepository, SolicitacaoContaRepository
    from app.controllers import AuthController, ChamadoController, SolicitacaoContaController
    from app.views import LoginWindow, UserWindow, AdminWindow, STYLESHEET
except ImportError as e:
    print(f"ERRO DE IMPORTAÇÃO: {e}")
    sys.exit(1)

class SistemaChamadosApp:
    def __init__(self):
        print(">>> Inicializando QApplication...", flush=True)
        self.app = QApplication(sys.argv)
        # Define ícone da aplicação (suporta executável empacotado)
        def resource_path(relative_path: str) -> str:
            if getattr(sys, 'frozen', False):
                base_path = getattr(sys, '_MEIPASS', os.path.abspath('.'))
            else:
                base_path = os.path.abspath('.')
            return os.path.join(base_path, relative_path)

        icon_path = resource_path('assets/icon.ico')
        try:
            if os.path.exists(icon_path):
                self.app.setWindowIcon(QIcon(icon_path))
        except Exception:
            pass
        self.app.setStyleSheet(STYLESHEET)
        
        # 1. Configuração do Banco
        print(">>> Configurando banco de dados...", flush=True)
        try:
            # Sem passar connection_string, ele lerá de variáveis de ambiente
            # Veja o arquivo .env na raiz do projeto para configurar
            self.db_manager = DatabaseManager()
            self.db_manager.setup()
            print(">>> Banco configurado com sucesso.", flush=True)
        except Exception as e:
            print(f"ERRO NO BANCO: {e}")
            raise e

        # 2. Repositórios e Controladores
        print(">>> Inicializando controladores...", flush=True)
        session_factory = self.db_manager.get_session
        user_repo = UsuarioRepository(session_factory)
        chamado_repo = ChamadoRepository(session_factory)
        solicitacao_repo = SolicitacaoContaRepository(session_factory)
        
        self.auth_controller = AuthController(user_repo)
        self.chamado_controller = ChamadoController(chamado_repo)
        self.solicitacao_controller = SolicitacaoContaController(solicitacao_repo)

        # 3. Janela Atual
        self.current_window = None
        print(">>> Abrindo janela de login...", flush=True)
        self.show_login()

    def show_login(self):
        # Abre nova janela antes de fechar a antiga
        new_window = LoginWindow(self.auth_controller, self.on_login_success)
        new_window.show()
        
        if self.current_window:
            self.current_window.close()
        self.current_window = new_window

    def on_login_success(self, user):
        # O Timer protege a transição, evitando crash no Linux ao apertar Enter
        QTimer.singleShot(0, lambda: self._perform_transition(user))

    def _perform_transition(self, user):
        try:
            print(f">>> Login sucesso: {user.nome} ({user.tipo})")
            if user.tipo == 1:
                # Admin
                new_window = AdminWindow(user, self.chamado_controller, self.logout)
                # INJEÇÃO DE DEPENDÊNCIAS EXTRAS PARA ADMIN
                new_window.set_auth_controller(self.auth_controller)
                new_window.set_solicitacao_controller(self.solicitacao_controller)
            else:
                # Comum
                new_window = UserWindow(user, self.chamado_controller, self.auth_controller, self.solicitacao_controller, self.logout)
            
            new_window.show()
            
            old_window = self.current_window
            self.current_window = new_window
            
            if old_window:
                old_window.close()
                
        except Exception as e:
            print(f"ERRO AO ABRIR PAINEL: {e}")
            traceback.print_exc()

    def logout(self):
        print(">>> Logout solicitado")
        self.auth_controller.logout()
        QTimer.singleShot(0, self.show_login)

    def run(self):
        print(">>> Entrando no loop de eventos...", flush=True)
        return self.app.exec()

if __name__ == "__main__":
    try:
        sistema = SistemaChamadosApp()
        sys.exit(sistema.run())
    except Exception as e:
        print("\n!!! OCORREU UM ERRO FATAL !!!")
        print(f"Erro: {e}")
        traceback.print_exc()