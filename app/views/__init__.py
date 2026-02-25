# views/__init__.py
# Este arquivo transforma a pasta 'views' em um módulo e exporta as classes
# para que o resto do seu projeto continue importando tudo de forma transparente,
# como se ainda fosse um único arquivo.

from .common import STYLESHEET, CenterMixin
from .auth import ChangePasswordDialog, LoginWindow
from .dialogs import UserEditDialog, TicketActionDialog, UserRegisterDialog, AccountRequestActionDialog
from .user import UserWindow
from .admin import AdminWindow
from .dashboard import DashboardWindow

__all__ = [
    "STYLESHEET",
    "CenterMixin",
    "ChangePasswordDialog",
    "LoginWindow",
    "UserEditDialog",
    "UserRegisterDialog",
    "AccountRequestActionDialog",
    "TicketActionDialog",
    "UserWindow",
    "AdminWindow",
    "DashboardWindow"
]