import sys
import os
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.mllp_client import MMLPClient  # noqa: E402


class FakeProcessor:
    def __init__(self):
        self.seen = []

    def process(self, hl7_message: str):
        self.seen.append(hl7_message)


class FakeSocket:
    def __init__(self, chunks):
        self.chunks = list(chunks)
        self.sent_data = []
        self.closed = False

    def recv(self, size):
        if not self.chunks:
            return b""
        return self.chunks.pop(0)

    def send(self, data):
        self.sent_data.append(data)

    def connect(self, addr):
        pass

    def close(self):
        self.closed = True


def frame(msg: str) -> bytes:
    return b"\x0b" + msg.encode("ascii") + b"\x1c\x0d"


def test_single_message_calls_processor_and_sends_ack():
    processor = FakeProcessor()
    client = MMLPClient(processor)

    hl7_msg = "MSH|TEST\rPID|1||123\r"
    fake_socket = FakeSocket([frame(hl7_msg)])

    client.sock = fake_socket
    client.running = True

    with pytest.raises(Exception):
        client._listen()

    assert processor.seen == [hl7_msg]
    assert len(fake_socket.sent_data) == 1


def test_multiple_messages_in_one_packet():
    processor = FakeProcessor()
    client = MMLPClient(processor)

    msg1 = "MSH|ONE\rPID|1||1\r"
    msg2 = "MSH|TWO\rPID|1||2\r"

    fake_socket = FakeSocket([frame(msg1) + frame(msg2)])

    client.sock = fake_socket
    client.running = True

    with pytest.raises(Exception):
        client._listen()

    assert processor.seen == [msg1, msg2]
    assert len(fake_socket.sent_data) == 2


def test_partial_packets_are_buffered():
    processor = FakeProcessor()
    client = MMLPClient(processor)

    msg = "MSH|PARTIAL\rPID|1||5\r"
    framed = frame(msg)

    fake_socket = FakeSocket([framed[:5], framed[5:]])

    client.sock = fake_socket
    client.running = True

    with pytest.raises(Exception):
        client._listen()

    assert processor.seen == [msg]
    assert len(fake_socket.sent_data) == 1


def test_send_ack_format():
    processor = FakeProcessor()
    client = MMLPClient(processor)

    fake_socket = FakeSocket([])
    client.sock = fake_socket

    client._send_ack()

    sent = fake_socket.sent_data[0]

    assert sent.startswith(b"\x0b")
    assert sent.endswith(b"\x1c\x0d")
    assert b"MSA|AA" in sent
