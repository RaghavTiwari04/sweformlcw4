## What's Done ✅

- [x] MLLP client - connects, receives messages, sends ACKs
- [x] HL7 parser - parses all three message types
- [x] Handling admissions and discharges
- [x] Architecture for the project
- [x] Testing for what was done

## TODO 🚧

1. **Preload history.csv into State Class and add necessary methods to handle it**
   - add tests

2. **When reciving creatine value we should launch a test** (`main.py`)
   - extract patient history from state.py
   - run inference from aki_detector.py
   - notify if positive with http_handler.py
   - add tests

3. **Make client resilient to server restarts**
   - This one is hard and requires managing again all the info the server will send without resending notifications
   - Add tests
4. **Make client resilient to client restarts**
   - For this i think we need to persists the state on a database or json
   - add tests

5. **Implement proper error handling in all classes**
   - Nice messages etc

6. **Add better comments to functions and classes**
   - Nice messages etc

7. **Integration Test**
   - I dont really know how to do this one

## Running

```bash
# Run unit tests
pytest tests/

# Run our code
python -m src.main
```

## Project Structure

```
swml_inference/
├── main.py              # Entry point - orchestrates everything
├── mllp_client.py       # Handles MLLP protocol communication
├── processor.py         # Parses HL7 messages into Python objects and handles tasks
├── http_handler.py      # Sends HTTP requests to pager system (TODO)
├── aki_detector.py      # AKI detection logic (TODO)
├── state.py             # Where the state is kept (NEEDS TODO)
└── tests/               # Unit tests with pytests
```

## Component Details

### 1. `mllp_client.py`

Handles the MLLP protocol for receiving HL7 messages over TCP. It puts the messages on a message queue so processor.py can access them.

**Key features:**

- Connects to hospital MLLP server
- Extracts messages between start block (`0x0b`) and end block (`0x1c`) markers
- Sends acknowledgements (ACK) back to confirm receipt

### 2. `processor.py`

Parses raw HL7 message strings into structured Python objects and handles them.

**Handles three message types:**

- `ADT^A01` - Patient admission (contains MRN, name, DOB, sex)
- `ADT^A03` - Patient discharge (contains MRN)
- `ORU^R01` - Blood test result (contains MRN, timestamp, creatinine value) (TODO)

### 3. `http_handler.py`

Sends HTTP POST requests to alert clinical teams about AKI events. (TODO)

### 4. `aki_detector.py`

This is where the ML model and AKI detection logic lives. (TODO)

### 5. `main.py`

Ties everything together in a main loop:

## Architecture Overview

```
┌─────────────────┐     MLLP/TCP      ┌──────────────────┐
│  Hospital PAS   │──────────────────▶│                  │
│  (Admissions)   │                   │                  │
└─────────────────┘                   │                  │
                                      │   Our System     │
┌─────────────────┐     MLLP/TCP      │                  │
│  Hospital LIMS  │──────────────────▶│  - MLLP Client   │
│  (Blood Tests)  │                   │  - HL7 Parser    │
└─────────────────┘                   │  - AKI Detector  │
                                      │  - Pager Client  │
                                      │                  │
┌─────────────────┐     HTTP POST     │                  │
│  Pager System   │◀──────────────────│                  │
└─────────────────┘                   └──────────────────┘
                                              ▲
                                              │
                                      ┌───────┴────────┐
                                      │ history.csv    │
                                      │ (historical    │
                                      │  blood tests)  │
                                      └────────────────┘
```
