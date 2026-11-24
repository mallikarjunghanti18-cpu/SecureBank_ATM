
import cv2


def detect_blink():

    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades +
        "haarcascade_frontalface_default.xml"
    )

    eye_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades +
        "haarcascade_eye.xml"
    )

    if face_cascade.empty() or eye_cascade.empty():
        print("Unable to load Haar Cascade models")
        return False, None

    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Webcam not available")
        return False, None

    blink_count = 0
    eyes_were_visible = False
    closed_frames = 0

    captured_frame = None

    try:
        while True:

            success, frame = cap.read()

            if not success:
                print("Unable to capture webcam frame")
                break

            gray = cv2.cvtColor(
                frame,
                cv2.COLOR_BGR2GRAY
            )

            faces = face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.3,
                minNeighbors=5
            )

            if len(faces) == 1:

                x, y, w, h = faces[0]

                face_gray = gray[y:y+h, x:x+w]

                eyes = eye_cascade.detectMultiScale(
                    face_gray,
                    scaleFactor=1.1,
                    minNeighbors=5,
                    minSize=(15, 15)
                )

                cv2.putText(
                    frame,
                    f"Eyes detected: {len(eyes)}",
                    (30, 100),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 255, 255),
                    2
            )

                for (ex, ey, ew, eh) in eyes:
                    cv2.rectangle(
                        frame,
                        (x + ex, y + ey),
                        (x + ex + ew, y + ey + eh),
                        (255, 0, 0),
                        2
                 )

                if len(eyes) >= 2:

                    if eyes_were_visible and closed_frames >= 2:
                        blink_count += 1

                    eyes_were_visible = True
                    closed_frames = 0

                elif eyes_were_visible:

                    closed_frames += 1

                cv2.rectangle(
                    frame,
                    (x, y),
                    (x+w, y+h),
                    (0, 255, 0),
                    2
                )

            else:
                eyes_were_visible = False
                closed_frames = 0

            cv2.putText(
                frame,
                f"Blinks: {blink_count}/2",
                (30, 50),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 255, 0),
                2
            )

            cv2.imshow(
                "SecureBank - Liveness Detection",
                frame
            )


            if blink_count >= 2:
                print("Two blinks detected!")

    # Capture a fresh frame after liveness verification
                for _ in range(5):
                    success, captured_frame = cap.read()

                if success and captured_frame is not None:
                    print("Live face captured successfully")

        # Save temporary frame for debugging
                    cv2.imwrite("live_face_debug.jpg", captured_frame)

                else:
                    captured_frame = None

                break

            if cv2.waitKey(1) & 0xFF == ord("q"):
                print("Authentication cancelled")
                break

        

    finally:
        cap.release()
        cv2.destroyAllWindows()

    if captured_frame is not None:
        print("Basic blink check passed")
        return True, captured_frame

    print("Basic blink check failed")
    return False, None
