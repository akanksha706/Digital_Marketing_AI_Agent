import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import httpx
from PIL import Image, ImageDraw, ImageFilter
import io
from app.core.config import settings

def test_dynamic():
    account_id = settings.CLOUDFLARE_ACCOUNT_ID
    token = settings.CLOUDFLARE_API_TOKEN

    prompt = "Look into this image and make the bubble come out from the orange color fish mouth."

    llama_url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/@cf/meta/llama-3.1-8b-instruct"
    sys_prompt = (
        "You are an AI visual editing parser. Given an image editing instruction, output ONLY a JSON object:\n"
        "{\n"
        '  "target": "mouth_or_hand_or_background_or_head",\n'
        '  "inpaint_prompt": "detailed visual description of what should be painted in that area",\n'
        '  "box": [ymin, xmin, ymax, xmax]\n'
        "}\n"
        "Where box contains float values from 0.0 to 1.0. For mouth/bubbles use [0.25, 0.35, 0.70, 0.70]. For hand use [0.10, 0.05, 0.40, 0.30]. Output ONLY valid JSON."
    )

    res = httpx.post(
        llama_url,
        headers={"Authorization": f"Bearer {token}"},
        json={
            "messages": [
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": prompt},
            ]
        },
        timeout=20.0,
    )
    print("LLaMA status:", res.status_code)
    raw = res.json().get("result", {}).get("response", "")
    print("LLaMA raw output:", raw)
    if isinstance(raw, dict):
        parsed = raw
    else:
        start = raw.find("{")
        end = raw.rfind("}") + 1
        parsed = json.loads(raw[start:end])
    print("Parsed JSON:", parsed)

    # Now execute inpainting
    inpaint_url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/@cf/runwayml/stable-diffusion-v1-5-inpainting"
    orig = Image.open(r"C:\Users\42WORKS\Downloads\fish.jpg").convert("RGB")
    img_512 = orig.resize((512, 512), Image.Resampling.LANCZOS)
    mask = Image.new("L", (512, 512), 0)
    draw = ImageDraw.Draw(mask)

    box = parsed.get("box", [0.25, 0.35, 0.70, 0.70])
    ymin, xmin, ymax, xmax = box
    draw.ellipse(
        [int(xmin * 512), int(ymin * 512), int(xmax * 512), int(ymax * 512)],
        fill=255,
    )

    buf_img = io.BytesIO()
    img_512.save(buf_img, format="PNG")
    buf_mask = io.BytesIO()
    mask.save(buf_mask, format="PNG")

    inpaint_prompt = parsed.get("inpaint_prompt", "stream of bubbles floating in water")
    print("Executing Cloudflare inpainting with prompt:", inpaint_prompt)

    inpaint_res = httpx.post(
        inpaint_url,
        headers={"Authorization": f"Bearer {token}"},
        json={
            "prompt": inpaint_prompt,
            "image": list(buf_img.getvalue()),
            "mask": list(buf_mask.getvalue()),
        },
        timeout=60.0,
    )
    print("Inpaint status:", inpaint_res.status_code)
    if inpaint_res.status_code == 200:
        with open("storage/dynamic_fish_bubbles.png", "wb") as f:
            f.write(inpaint_res.content)
        print("SUCCESS! Saved storage/dynamic_fish_bubbles.png")

if __name__ == "__main__":
    test_dynamic()
