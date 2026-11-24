
from backend.authentication.liveness_detection import detect_blink
from backend.authentication.face_auth import authenticate_face


def authenticate_customer(email,captured_frame=None):

    print("\nStarting customer authentication...")

    # Check 1: Live blink detection and automatic capture
    print("\nStep 1: Checking liveness...")

    liveness_result, captured_frame = detect_blink()

    if not liveness_result or captured_frame is None:
        return False, "Liveness check failed"

    print("Liveness check successful")

    # Check 2: Match the fresh webcam frame
    print("\nStep 2: Checking registered face...")

    face_result, message = authenticate_face(email, captured_frame)

    if not face_result:
        return False, message

    print("Face matching successful")

    return True, "Customer authentication successful"
