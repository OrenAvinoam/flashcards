from contextvars import ContextVar

current_token: ContextVar[str] = ContextVar("current_token", default="")
