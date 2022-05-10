from typing import Dict, List, Set


def scope2dict(scopes: List[str]) -> Dict[str, Set]:
    """Given a list of scopes like ["admin:write", "user:read"]
    it will returns a dictionary where the namespace is the key and the actions
    turns into a set"""
    permissions: Dict[str, Set] = {}
    for s in scopes:
        try:
            ns, action = s.split(":", maxsplit=1)
        except ValueError:
            ns = s
            action = "any"
        ns = ns if ns else "any"
        actions = {a for a in action.split(":")}
        permissions[ns] = actions
    return permissions


def validate(
    scopes: List[str],
    user_scopes: List[str],
    require_all=True,
    require_all_actions=True,
) -> bool:
    """
    from sanic_jwt
    the idea is to provide a scoped access to different resources
    """
    user_perms = scope2dict(user_scopes)
    required = scope2dict(scopes)
    names = {k for k in user_perms.keys()}
    required_names = {k for k in required.keys()}
    intersection = required_names.intersection(names)
    if require_all:
        if len(required_names) != len(intersection) and "any" not in required.keys():
            return False
    elif intersection == 0 and "any" not in required.keys():
        return False

    _match = 0
    for ns in intersection:
        actions_matched = required[ns].intersection(user_perms[ns])
        if len(actions_matched) > 0 or "any" in required[ns]:
            _match += 1
    if _match == 0:
        return False
    return True
