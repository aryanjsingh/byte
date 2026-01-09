"""
Image Generation Tool using Gemini Imagen API
Generates images when user prompts end with '-gen'
"""
import os
import base64
from typing import Optional
from langchain_core.tools import tool
from dotenv import load_dotenv

load_dotenv()


def generate_image_with_imagen(prompt: str) -> Optional[dict]:
    """
    Generate an image using Google's Imagen model via the new genai SDK.
    
    Args:
        prompt: Description of the image to generate
    
    Returns:
        Dict with 'image_base64' and 'mime_type' or None on failure
    """
    try:
        from google import genai
        from google.genai import types
        
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("❌ No GOOGLE_API_KEY found")
            return None
        
        client = genai.Client(api_key=api_key)
        
        print(f"🎨 Generating image with prompt: {prompt}")
        
        # Use Imagen 4 Fast model
        response = client.models.generate_images(
            model="imagen-4.0-fast-generate-001",
            prompt=prompt,
            config=types.GenerateImagesConfig(
                number_of_images=1,
                aspect_ratio="16:9",
                safety_filter_level="BLOCK_LOW_AND_ABOVE",
                person_generation="ALLOW_ADULT",
            )
        )
        
        if response.generated_images and len(response.generated_images) > 0:
            image = response.generated_images[0]
            # Get base64 encoded image
            img_base64 = base64.b64encode(image.image.image_bytes).decode('utf-8')
            
            print(f"✅ Image generated successfully!")
            return {
                "image_base64": img_base64,
                "mime_type": "image/png"
            }
        else:
            print("❌ No image generated")
            return None
            
    except Exception as e:
        print(f"❌ Image generation error: {e}")
        import traceback
        traceback.print_exc()
        return None


@tool
def image_gen(prompt: str) -> str:
    """
    Generate an image based on a text prompt using Gemini Imagen 3.
    Use this tool when users end their message with '-gen' suffix.
    
    Examples:
    - "a cute cat -gen" → Generate image of a cute cat
    - "cybersecurity shield logo -gen" → Generate a cybersecurity logo
    - "sunset over mountains -gen" → Generate landscape image
    
    Returns a JSON string with the generated image data (base64).
    """
    print(f"🔧 TOOL CALLED: image_gen")
    print(f"📝 Prompt: {prompt}")
    
    # Remove -gen suffix if still present
    clean_prompt = prompt.replace("-gen", "").strip()
    
    result = generate_image_with_imagen(clean_prompt)
    
    if not result:
        return '{"type": "image_gen_error", "error": "Failed to generate image"}'
    
    import json
    return json.dumps({
        "type": "image_gen_result",
        "image_base64": result["image_base64"],
        "mime_type": result["mime_type"],
        "prompt": clean_prompt
    })
