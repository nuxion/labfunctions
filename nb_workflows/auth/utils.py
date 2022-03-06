from nb_workflows.conf.server_settings import settings
from nb_workflows.hashes import PasswordScript


def password_manager() -> PasswordScript:
    s = settings.SALT
    return PasswordScript(salt=s.encode("utf-8"))
