import sys
import os
from datetime import datetime
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))  # noqa: E402
from src.processor import Processor  # noqa: E402


class MockHttp:
    def __init__(self):
        self.sent = []

    def send(self, payload):
        self.sent.append(payload)


class MockDetector:
    def __init__(self, value=False):
        self.value = value

    def predict(self, lab_entry):
        return self.value


class MockState:
    def __init__(self):
        self.data = {
            "admitted_patients": [],
            "processed_messages": [],
            "paged_patients": [],
            "lab_history": {},
        }

    def admit(self, mrn, sex):
        if mrn not in self.data["admitted_patients"]:
            self.data["admitted_patients"].append(mrn)
        if mrn not in self.data["lab_history"]:
            self.data["lab_history"][mrn] = {
                "min": 10000,
                "mean": 0,
                "max": 0,
                "median": 0,
                "std": 0,
                "sum": 0,
                "results": [],
            }
        self.data["lab_history"][mrn]["sex"] = 0 if sex == "F" else 1

    def discharge(self, mrn):
        if mrn in self.data["admitted_patients"]:
            self.data["admitted_patients"].remove(mrn)

    def add_creatinine(self, mrn, value):
        self.data["lab_history"][mrn]["results"].append(value)

    def is_processed(self, mid):
        return mid in self.data["processed_messages"]

    def mark_processed(self, mid):
        self.data["processed_messages"].append(mid)

    def paged_patient(self, mrn):
        self.data["paged_patients"].append(mrn)

    def has_paged_patient(self, mrn):
        return mrn in self.data["paged_patients"]


@pytest.fixture
def state():
    return MockState()


@pytest.fixture
def http():
    return MockHttp()


def test_parse_admission():
    p = Processor(None, None, None)

    msg = (
        "MSH|^~\\&|SIM|HOSP|||202402011200||ADT^A01|MSG001|2.5\r"
        "PID|1||81299001||NAME||19910517|M\r"
    )

    r = p._parse_message(msg)

    assert r["type"] == "ADT^A01"
    assert r["mrn"] == "81299001"
    assert r["msg_id"] == "MSG001"
    assert r["dob"] == datetime(1991, 5, 17)
    assert r["sex"] == "M"


def test_parse_discharge():
    p = Processor(None, None, None)

    msg = "MSH|^~\\&|SIM|HOSP|||202402011300||ADT^A03|MSG002|2.5\r" "PID|1||77788\r"

    result = p._parse_message(msg)

    assert result["type"] == "ADT^A03"
    assert result["mrn"] == "77788"
    assert result["msg_id"] == "MSG002"


def test_parse_creatinine():
    p = Processor(None, None, None)

    msg = (
        "MSH|^~\\&|SIMULATION|SOUTH RIVERSIDE|||202401201800||ORU^R01|MSG003|2.5\r"
        "PID|1||4567\r"
        "OBR|1||||||20240201201530\r"
        "OBX|1|SN|CREATININE||88.9\r"
    )

    r = p._parse_message(msg)

    assert r["type"] == "ORU^R01"
    assert r["mrn"] == "4567"
    assert r["is_creatinine"] is True
    assert r["result"] == 88.9
    assert r["time"] == "20240201201530"


def test_admission_flow(state, http):
    p = Processor(state, MockDetector(False), http)

    p._handle_message({"type": "ADT^A01", "mrn": "1", "sex": "M"})
    assert state.data["admitted_patients"] == ["1"]


def test_parse_non_creatinine():
    p = Processor(None, None, None)

    msg = (
        "MSH|^~\\&|SIMULATION|SOUTH RIVERSIDE|||202401201800||ORU^R01|MSG004|2.5\r"
        "PID|1||4567\r"
        "OBR|1||||||20240201201530\r"
        "OBX|1|SN|POTASSIUM||4.1\r"
    )

    result = p._parse_message(msg)

    # In the refactored code, non-creat keeps the original type but sets a flag or updates type
    assert result["type"] == "NON_CREAT"
    assert result["mrn"] == "4567"


def test_handle_admission_updates_state(state, http):
    detector = MockDetector(False)
    processor = Processor(state, detector, http)

    processor._handle_message({"type": "ADT^A01", "mrn": "1", "sex": "M"})

    assert state.data["admitted_patients"] == ["1"]


def test_handle_discharge_updates_state(state, http):
    detector = MockDetector(False)
    processor = Processor(state, detector, http)

    state.admit("2", "F")

    processor._handle_message({"type": "ADT^A03", "mrn": "2"})

    assert state.data["admitted_patients"] == []


def test_persistence_skips_processed_messages(state, http):
    detector = MockDetector(False)
    processor = Processor(state, detector, http)

    msg_id = "EXISTING_ID"
    state.mark_processed(msg_id)

    msg = (
        f"MSH|^~\\&|SIM|HOSP|||202402011200||ADT^A01|{msg_id}|P|2.5\r"
        "PID|1||999||NAME||19910517|M\r"
    )

    processor.process(msg)

    # Should NOT be admitted because already processed
    assert "999" not in state.data["admitted_patients"]
    assert state.data["processed_messages"].count(msg_id) == 1


def test_malformed_messages_return_empty_dict(state, http):
    detector = MockDetector(False)
    processor = Processor(state, detector, http)

    bad_msg = "MSH|BAD|DATA"

    result = processor._parse_message(bad_msg)

    assert result == {}
