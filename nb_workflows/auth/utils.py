from nb_workflows.conf import settings
from nb_workflows.hashes import PasswordScript


def password_manager() -> PasswordScript:
    s = settings.SALT
    return PasswordScript(salt=s.encode("utf-8"))
