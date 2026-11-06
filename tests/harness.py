"""Fake Telegram objects — snake_core.py ko bina bot token ke test karne ke liye.

Koi network nahi, koi real Telegram nahi. Sirf jitna snake_core use karta hai
utna hi banaya gaya hai.
"""
import os
import sys
import types

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

ADMIN = 8999053405


class FakeMessage:
    def __init__(self, text="", sink=None):
        self.text = text
        self.sink = sink if sink is not None else []
        self.replies = self.sink

    async def reply_text(self, text, **kw):
        self.sink.append(("text", text, kw))
        return FakeMessage(text, self.sink)

    async def reply_document(self, document=None, filename=None, caption=None, **kw):
        self.sink.append(("doc", caption or filename, kw))
        return FakeMessage(caption, self.sink)

    async def edit_text(self, text, **kw):
        self.sink.append(("edit", text, kw))
        return FakeMessage(text, self.sink)

    async def delete(self, **kw):
        self.sink.append(("delete", "", {}))
        return True

    async def answer(self, *a, **k):
        return True


class FakeQuery:
    def __init__(self, data, sink):
        self.data = data
        self.sink = sink
        self.message = FakeMessage("", sink)

    async def answer(self, *a, **k):
        return True

    async def edit_message_text(self, text, **kw):
        self.sink.append(("edit", text, kw))
        return FakeMessage(text, self.sink)

    async def edit_message_reply_markup(self, **kw):
        self.sink.append(("markup", "", kw))
        return True

    async def delete_message(self, **kw):
        self.sink.append(("delete", "", {}))
        return True


class FakeDocument:
    def __init__(self, name, data, size=None):
        self.file_name = name
        self._data = data
        self.file_size = size if size is not None else len(data)

    async def get_file(self):
        me = self

        class F:
            async def download_as_bytearray(self):
                return bytearray(me._data)
        return F()


class FakeUser:
    def __init__(self, uid=ADMIN, first_name="Tester", username="tester"):
        self.id = uid
        self.first_name = first_name
        self.username = username
        self.mention_html = lambda *a, **k: "@%s" % username


class FakeChat:
    def __init__(self, cid=ADMIN):
        self.id = cid
        self.type = "private"


class FakeUpdate:
    def __init__(self, uid=ADMIN, text=None, data=None, doc=None):
        self.sink = []
        self.effective_user = FakeUser(uid)
        self.effective_chat = FakeChat(uid)
        self.callback_query = FakeQuery(data, self.sink) if data is not None else None
        self.message = None
        if text is not None or doc is not None:
            self.message = FakeMessage(text or "", self.sink)
            if doc is not None:
                self.message.document = doc
            if text is not None:
                self.message.text = text
        self.effective_message = self.callback_query or self.message

    # helpers
    def texts(self):
        return [t for kind, t, _ in self.sink if kind in ("text", "edit")]

    def last_text(self):
        t = self.texts()
        return t[-1] if t else ""

    def docs(self):
        return [t for kind, t, _ in self.sink if kind == "doc"]


class FakeBot:
    def __init__(self):
        self.id = 1
        self.username = "test_bot"

    async def send_message(self, *a, **k):
        return FakeMessage()


class FakeContext:
    def __init__(self, user_data=None, args=None):
        self.user_data = user_data if user_data is not None else {}
        self.user_data.setdefault("verified", True)   # captcha skip
        self.chat_data = {}
        self.bot_data = {}
        self.args = args or []
        self.bot = FakeBot()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False


def load_core():
    """snake_core import karo (data dir temp me)."""
    import snake_core
    return snake_core
