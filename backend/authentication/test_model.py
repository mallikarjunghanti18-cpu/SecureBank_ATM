
import mediapipe as mp

MODEL_PATH = "backend/models/face_landmarker.task"

BaseOptions = mp.tasks.BaseOptions
FaceLandmarker = mp.tasks.vision.FaceLandmarker
Options = mp.tasks.vision.FaceLandmarkerOptions

options = Options(
    base_options=BaseOptions(
        model_asset_path=MODEL_PATH
    ),
    num_faces=1
)

print("Loading Face Landmarker model...")

with FaceLandmarker.create_from_options(options) as landmarker:
    print("Face Landmarker model loaded successfully!")
