
from backend.authentication.liveness_detection import detect_blink

print("Starting SecureBank liveness detection...")

result = detect_blink()

print("Liveness result:", result)
