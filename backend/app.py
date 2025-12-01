import os
import json
import base64
from flask import Flask, request, jsonify, send_from_directory
from google import genai
from google.genai import types

app = Flask(__name__, static_folder='../frontend', static_url_path='/')

# Initialize Google Gen AI Client
# Ensure GOOGLE_API_KEY is set in your environment variables
client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))

@app.route('/')
def home():
    """Serve the frontend"""
    return send_from_directory('../frontend', 'index.html')

@app.route('/generate', methods=['POST'])
def generate_card():
    data = request.json
    base = data.get('base', 'Monster')
    element = data.get('element', 'Normal')
    color = data.get('color', 'Grey')
    feature = data.get('feature', 'None')

    # 1. Generate Card Stats & Text (Using a fast text model)
    # We ask for a JSON response for easy parsing
    text_prompt = f"""
    Create a Pokemon based on: {base}, Element: {element}, Color: {color}, Feature: {feature}.
    Return ONLY a JSON object with keys: 'name' (creative name), 'hp' (number), 'description' (max 20 words flavor text).
    """
    
    text_resp = client.models.generate_content(
        model="gemini-2.5-flash-lite",
        contents=text_prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json"
        )
    )
    
    card_data = json.loads(text_resp.text)

    # 2. Generate Image using Gemini 3 Pro Image (Nano Banana Pro)
    # The model ID 'gemini-3-pro-image-preview' is the specific reference requested
    image_prompt = f"""
    Official Pokemon card art of a {color} {element} type creature resembling {base} with {feature}. 
    Ken Sugimori style, high quality, white background, dynamic pose.
    """
    
    image_resp = client.models.generate_content(
        model="gemini-3-pro-image-preview",
        contents=image_prompt
    )

    # Extract base64 image from response
    # Note: The API structure for images might vary slightly in preview SDKs; 
    # this assumes standard inline_data return.
    try:
        image_bytes = image_resp.candidates[0].content.parts[0].inline_data.data
        # If it returns bytes, we might need to base64 encode it depending on the SDK version
        # The 'inline_data.data' is usually already bytes or a b64 string. 
        # Assuming bytes here -> convert to b64 string for JSON
        if isinstance(image_bytes, bytes):
            image_b64 = base64.b64encode(image_bytes).decode('utf-8')
        else:
            image_b64 = image_bytes # It might already be a string
    except Exception as e:
        print(f"Image gen error: {e}")
        # Fallback empty image if generation fails
        image_b64 = ""

    return jsonify({
        "name": card_data.get('name'),
        "hp": card_data.get('hp'),
        "element": element,
        "description": card_data.get('description'),
        "image_b64": image_b64
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
