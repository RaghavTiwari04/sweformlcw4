

import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.main import InferenceService  # noqa: E402


class FakeState:
    pass


class FakeDetector:
    pass


class FakeHttp:
    pass


class FakeProcessor:
    def __init__(self, state, detector, http):
        self.state = state
        self.detector = detector
        self.http = http


class FakeMMLPClient:
    def __init__(self, processor):
        self.processor = processor
        self.started = False

    def start(self):
        self.started = True


def test_inference_service_wires_dependencies(monkeypatch):
    monkeypatch.setattr("src.main.State", FakeState)
    monkeypatch.setattr("src.main.AKIDetector", FakeDetector)
    monkeypatch.setattr("src.main.HttpHandler", FakeHttp)
    monkeypatch.setattr("src.main.Processor", FakeProcessor)
    monkeypatch.setattr("src.main.MMLPClient", FakeMMLPClient)

    service = InferenceService()

    assert isinstance(service.state, FakeState)
    assert isinstance(service.aki_detector, FakeDetector)
    assert isinstance(service.http_handler, FakeHttp)

    assert isinstance(service.processor, FakeProcessor)
    assert service.processor.state is service.state
    assert service.processor.detector is service.aki_detector
    assert service.processor.http is service.http_handler

    assert isinstance(service.mmlp_client, FakeMMLPClient)
    assert service.mmlp_client.processor is service.processor


def test_start_inference_service_starts_mllp_client(monkeypatch):
    monkeypatch.setattr("src.main.State", FakeState)
    monkeypatch.setattr("src.main.AKIDetector", FakeDetector)
    monkeypatch.setattr("src.main.HttpHandler", FakeHttp)
    monkeypatch.setattr("src.main.Processor", FakeProcessor)
    monkeypatch.setattr("src.main.MMLPClient", FakeMMLPClient)

    service = InferenceService()

    def fake_sleep(_):
        raise KeyboardInterrupt  # break infinite loop immediately

    monkeypatch.setattr("time.sleep", fake_sleep)

    service.start_inference_service()

    assert service.mmlp_client.started is True


def test_keyboard_interrupt_is_handled(monkeypatch, capsys):
    monkeypatch.setattr("src.main.State", FakeState)
    monkeypatch.setattr("src.main.AKIDetector", FakeDetector)
    monkeypatch.setattr("src.main.HttpHandler", FakeHttp)
    monkeypatch.setattr("src.main.Processor", FakeProcessor)
    monkeypatch.setattr("src.main.MMLPClient", FakeMMLPClient)

    service = InferenceService()

    monkeypatch.setattr("time.sleep", lambda _: (_ for _ in ()).throw(KeyboardInterrupt))

    service.start_inference_service()

    captured = capsys.readouterr()
    assert "Service shutting down" in captured.out
