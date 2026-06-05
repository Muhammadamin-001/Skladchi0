from urllib.parse import urlencode

import telebot

from config.settings import WEB_APP_URL


ROLE_LABELS = {
    "admin": "admin",
    "employee": "xodim",
    "customer": "mijoz",
}


def get_app_url(role=None):
    """Web/Telegram Mini App uchun rolga mos login havolasini qaytaradi."""
    if not WEB_APP_URL:
        return None
    params = {}
    if role:
        params["role"] = role
    query = f"?{urlencode(params)}" if params else ""
    return f"{WEB_APP_URL}/login{query}"


def get_app_button_kwargs(role=None):
    """InlineKeyboardButton uchun Mini App yoki oddiy URL parametrlarini tayyorlaydi."""
    url = get_app_url(role)
    if not url:
        return None
    if hasattr(telebot.types, "WebAppInfo"):
        return {"web_app": telebot.types.WebAppInfo(url)}
    return {"url": url}


def make_login_message(role, login, password=None):
    """Foydalanuvchiga web ilova havolasi va kerak bo'lsa login ma'lumotini yozadi."""
    role_label = ROLE_LABELS.get(role, role or "foydalanuvchi")
    lines = [
        "✅ Siz tasdiqlandingiz!",
        f"👤 Toifa: <b>{role_label}</b>",
    ]
    url = get_app_url(role)
    if url:
        lines.append(f"📱 Ilova: {url}")
    else:
        lines.append("📱 Ilova havolasi hali sozlanmagan. Admin WEB_APP_URL ni .env/Render envda kiritsin.")
    if password:
        lines.extend([
            "",
            f"🔐 Login: <code>{login}</code>",
            f"🔑 Parol: <code>{password}</code>",
        ])
    if role == "employee":
        lines.append("\nBotdagi xodim paneli uchun /start bosing.")
    return "\n".join(lines)
