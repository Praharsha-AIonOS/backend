# services/model_client.py

import requests

MODEL_ENDPOINT = "http://154.201.127.0:7001/generate"


def call_lipsync_model(input_video: str, input_audio: str):
    with open(input_video, "rb") as v, open(input_audio, "rb") as a:
        response = requests.post(
            MODEL_ENDPOINT,
            files={
                "media": ("input.mp4", v, "video/mp4"),
                "audio": ("input.wav", a, "audio/wav")
            }
        )

    print("====== MODEL RESPONSE DEBUG ======")
    print("Status Code:", response.status_code)
    print("Headers:", response.headers)
    print("Text:", response.text)
    print("Raw Bytes Length:", len(response.content))
    print("==================================")

    return response.json()
