import os
from huggingface_hub import InferenceClient

HF_TOKEN = os.getenv("HF_TOKEN")

if not HF_TOKEN:
    raise RuntimeError("HF_TOKEN not found. Set your Hugging Face token first.")

client = InferenceClient(
    provider="auto",
    api_key=HF_TOKEN,
)

prompt = """
A cinematic shot of a futuristic Mumbai street at night,
neon lights, rainy road reflections, slow camera movement,
high detail, realistic, 480p
"""

print("Generating video... this may take time.")

video_bytes = client.text_to_video(
    prompt,
    model="Wan-AI/Wan2.1-T2V-1.3B",
)

output_path = "wan_test_output.mp4"

with open(output_path, "wb") as f:
    f.write(video_bytes)

print(f"Done. Saved as {output_path}")
