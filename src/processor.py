import hl7
import hashlib
from datetime import datetime
from typing import Any


class Processor:
    def __init__(self, state, aki_detector, http_handler):
        self.state = state
        self.detector = aki_detector
        self.http = http_handler

    def process(self, hl7_message: str):
        # Parse raw HL7 into normalized dict
        parsed = self._parse_message(hl7_message)

        if not parsed:
            return

        msg_id = parsed["msg_id"]

        # Prevent reprocessing duplicate HL7 transmissions
        if self.state.is_processed(msg_id):
            print(f"Skipping duplicate {msg_id}")
            return

        if self._handle_message(parsed):
            self.state.mark_processed(msg_id)

    def _parse_message(self, hl7_message: str) -> dict[str, Any]:
        try:
            msg = hl7.parse(hl7_message.strip())
            msh = msg.segments("MSH")[0]
            pid = msg.segments("PID")[0]

            msg_id = str(msh[10]) or hashlib.md5(hl7_message.encode()).hexdigest()
            message_type = str(msh[9])
            mrn = str(pid[3])

            result = {
                "msg_id": msg_id,
                "type": message_type,
                "mrn": mrn,
            }

            # Admission event
            if message_type == "ADT^A01":
                if len(pid) > 7 and str(pid[7]):
                    result["dob"] = datetime.strptime(str(pid[7]), "%Y%m%d")
                if len(pid) > 8:
                    result["sex"] = str(pid[8])
                return result

            # Discharge event
            if message_type == "ADT^A03":
                return result

            # Lab result message
            if message_type == "ORU^R01":
                obx = msg.segments("OBX")[0]
                obr = msg.segments("OBR")[0]

                if str(obx[3]) == "CREATININE":
                    result.update({
                        "is_creatinine": True,
                        "result": float(str(obx[5][0])),
                        "time": str(obr[7]),
                    })
                else:
                    result["type"] = "NON_CREAT"

                return result

            return {}

        except Exception as e:
            print(f"Parse error: {e}")
            return {}

    def _handle_message(self, message: dict[str, Any]) -> bool:
        m_type = message["type"]
        mrn = message["mrn"]

        if m_type == "ADT^A01":
            self.state.admit(mrn, message.get("sex"))
            print(f"Admitted {mrn}")
            return True

        if m_type == "ADT^A03":
            self.state.discharge(mrn)
            print(f"Discharged {mrn}")
            return True

        if m_type == "ORU^R01" and message.get("is_creatinine"):
            # Ignore labs for patients not currently admitted
            if not self.state.has_patient(mrn):
                print("Ignoring lab — patient not admitted")
                return False

            self.state.add_creatinine(mrn, message["result"])

            labs = self.state.get_lab_history(mrn)

            if labs:
                aki = self.detector.predict(labs)
                # Page once per admission if AKI detected
                if aki and not self.state.has_paged_patient(mrn):
                    payload = f"{mrn},{message['time']}"
                    self.http.send(payload)
                    self.state.paged_patient(mrn)

            return True

        return False