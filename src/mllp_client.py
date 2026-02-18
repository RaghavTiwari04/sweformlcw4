import socket
import time
import os
import threading
from .server_state import set_server_running


class MMLPClient(threading.Thread):
    # MLLP framing bytes per HL7 over TCP spec
    MLLP_START_OF_BLOCK = b"\x0b"
    MLLP_END_OF_BLOCK = b"\x1c"
    MLLP_CARRIAGE_RETURN = b"\x0d"
    MLLP_BUFFER_SIZE = 1024

    def __init__(self, processor):
        super().__init__(daemon=True)
        # Expected format: host:port (defaults to localhost:8440)
        addr = os.environ.get("MLLP_ADDRESS", "localhost:8440")

        if ":" in addr:
            self.host, port = addr.split(":")
            self.port = int(port)
        else:
            self.host = addr
            self.port = 8440

        self.processor = processor
        # Accumulates partial TCP frames until full MLLP message received
        self.buffer = b""
        self.running = True

    def run(self):
        # Persistent reconnect loop
        self._connection_manager()

    def _connection_manager(self):
        while self.running:
            try:
                print(f"MMLP connecting to {self.host}:{self.port}")
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.sock.connect((self.host, self.port))

                set_server_running(True)
                # Block until disconnect or error
                self._listen()

            except Exception as e:
                print(f"MMLP disconnected: {e}")
                set_server_running(False)
                self.buffer = b""
                try:
                    self.sock.close()
                except Exception:
                    pass
                # Backoff before reconnect
                time.sleep(5)

    def _listen(self):
        while self.running:
            chunk = self.sock.recv(self.MLLP_BUFFER_SIZE)
            if not chunk:
                # Server closed TCP connection
                raise Exception("Server closed connection")

            self.buffer += chunk

            # Extract all complete MLLP frames in buffer
            while True:
                start = self.buffer.find(self.MLLP_START_OF_BLOCK)
                end = self.buffer.find(self.MLLP_END_OF_BLOCK)

                if start == -1 or end == -1:
                    break

                # HL7 payload without framing bytes
                payload = self.buffer[start + 1:end]
                # Skip past <FS><CR>
                self.buffer = self.buffer[end + 2:]

                # Process decoded HL7 message
                self.processor.process(payload.decode("ascii"))
                self._send_ack()

    def _send_ack(self):
        body = "MSH|^~\\&|||||||ACK|||2.5\rMSA|AA\r".encode()

        framed = (
            self.MLLP_START_OF_BLOCK
            + body
            + self.MLLP_END_OF_BLOCK
            + self.MLLP_CARRIAGE_RETURN
        )

        self.sock.send(framed)
