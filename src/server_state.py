import threading

# Thread-safe global flag
_server_running = True
_lock = threading.Lock()


def is_server_running() -> bool:
    with _lock:
        return _server_running


def set_server_running(value: bool):
    global _server_running
    with _lock:
        _server_running = value