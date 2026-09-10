from .i18n import get_translations


def language(request):
    lang = request.session.get("lang", "sk")
    path = request.path

    if path.startswith("/search"):
        active_tab = "search"
    elif path.startswith("/jobs"):
        active_tab = "jobs"
    elif path.startswith("/offline"):
        active_tab = "offline"
    else:
        active_tab = "library"

    return {
        "lang": lang,
        "T": get_translations(lang),
        "active_tab": active_tab,
    }