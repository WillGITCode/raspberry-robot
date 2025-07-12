from vosk import Model, KaldiRecognizer
import pyaudio
import json
from control.xbox_controller import XboxControllerSingleton


def handle_controller_input(controller):
    """Process controller input and update state machine as needed."""
    if controller.get_property('Back'):
        return False  # Signal to exit main loop

    return True

model = Model("sensorTests/model")
rec = KaldiRecognizer(model, 16000)
controller = XboxControllerSingleton()
running = True

p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000,
                input=True, frames_per_buffer=8000)
stream.start_stream()

print("Listening...")

try:
    while running:
        running = handle_controller_input(controller)
      
        data = stream.read(4000, exception_on_overflow=False)

        if rec.AcceptWaveform(data):
            result = json.loads(rec.Result())
            print("You said:", result.get("text", ""))
except Exception as e:
    print("Stopped.")
