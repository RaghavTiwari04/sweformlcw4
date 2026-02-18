from .processor import Processor
from .http_handler import HttpHandler
from .state import State
from .mllp_client import MMLPClient
from .aki_detector import AKIDetector
import time


class InferenceService:
    def __init__(self):
        self.state = State()
        self.aki_detector = AKIDetector()

        self.http_handler = HttpHandler()
        self.processor = Processor(
            self.state,
            self.aki_detector,
            self.http_handler,
        )

        self.mmlp_client = MMLPClient(self.processor)

    def start_inference_service(self):
        self.mmlp_client.start()   # starts background socket thread

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("Service shutting down...")


if __name__ == "__main__":
    service = InferenceService()
    service.start_inference_service()
