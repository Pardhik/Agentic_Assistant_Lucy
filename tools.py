import cv2
import base64
import os
from dotenv import load_dotenv
from groq import Groq

# Load environment variables
load_dotenv()

def capture_image() -> str:
    """
    Captures one frame from the default webcam (Windows-friendly),
    resizes it, encodes it as Base64 JPEG, and returns it as a string.
    """
    # Try both DirectShow (Windows) and default backend
    backends = [cv2.CAP_DSHOW, cv2.CAP_ANY]

    for backend in backends:
        for idx in range(4):  # Try first 4 indices
            cap = cv2.VideoCapture(idx, backend)
            if cap.isOpened():
                # Warm up
                for _ in range(10):
                    cap.read()
                ret, frame = cap.read()
                cap.release()

                if not ret:
                    continue

                # Save sample for debug (optional)
                cv2.imwrite("sample2.jpg", frame)

                # Encode as Base64 JPEG
                ret, buf = cv2.imencode(".jpg", frame)
                if ret:
                    return base64.b64encode(buf).decode("utf-8")

    raise RuntimeError("Could not open any webcam (tried indices 0-3 with multiple backends)")


def analyze_image_with_query(query: str) -> str:
    """
    Takes a text query, captures an image, and sends both
    to Groq's multimodal chat API for analysis.
    """
    img_b64 = capture_image()
    model = "meta-llama/llama-4-maverick-17b-128e-instruct"

    if not query or not img_b64:
        return "Error: both 'query' and 'image' are required."

    client = Groq()

    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": query},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"},
                },
            ],
        }
    ]

    chat_completion = client.chat.completions.create(
        messages=messages,
        model=model,
    )

    return chat_completion.choices[0].message.content

"""
if __name__ == "__main__":
    query = "How many people do you see?"
    try:
        print(analyze_image_with_query(query))
    except Exception as e:
        print(f"Error: {e}")
"""