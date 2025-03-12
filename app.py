from base64 import b64decode
import gradio as gr
import io
import json
from PIL import Image
import requests

IONOS_API_TOKEN = "eyJ0eXAiOiJKV1QiLCJraWQiOiI0M2FlNjY0ZC03ZWFlLTQ0ODctOGVjOS1mNzYxMGJkNWY1ZTgiLCJhbGciOiJSUzI1NiJ9.eyJpc3MiOiJpb25vc2Nsb3VkIiwiaWF0IjoxNzM3ODkwODE0LCJjbGllbnQiOiJVU0VSIiwiaWRlbnRpdHkiOnsicm9sZSI6Im93bmVyIiwiY29udHJhY3ROdW1iZXIiOjM1MDEyODQ5LCJpc1BhcmVudCI6ZmFsc2UsInByaXZpbGVnZXMiOlsiREFUQV9DRU5URVJfQ1JFQVRFIiwiU05BUFNIT1RfQ1JFQVRFIiwiSVBfQkxPQ0tfUkVTRVJWRSIsIk1BTkFHRV9EQVRBUExBVEZPUk0iLCJBQ0NFU1NfQUNUSVZJVFlfTE9HIiwiUENDX0NSRUFURSIsIkFDQ0VTU19TM19PQkpFQ1RfU1RPUkFHRSIsIkJBQ0tVUF9VTklUX0NSRUFURSIsIkNSRUFURV9JTlRFUk5FVF9BQ0NFU1MiLCJLOFNfQ0xVU1RFUl9DUkVBVEUiLCJGTE9XX0xPR19DUkVBVEUiLCJBQ0NFU1NfQU5EX01BTkFHRV9NT05JVE9SSU5HIiwiQUNDRVNTX0FORF9NQU5BR0VfQ0VSVElGSUNBVEVTIiwiQUNDRVNTX0FORF9NQU5BR0VfTE9HR0lORyIsIk1BTkFHRV9EQkFBUyIsIkFDQ0VTU19BTkRfTUFOQUdFX0ROUyIsIk1BTkFHRV9SRUdJU1RSWSIsIkFDQ0VTU19BTkRfTUFOQUdFX0NETiIsIkFDQ0VTU19BTkRfTUFOQUdFX1ZQTiIsIkFDQ0VTU19BTkRfTUFOQUdFX0FQSV9HQVRFV0FZIiwiQUNDRVNTX0FORF9NQU5BR0VfTkdTIiwiQUNDRVNTX0FORF9NQU5BR0VfS0FBUyIsIkFDQ0VTU19BTkRfTUFOQUdFX05FVFdPUktfRklMRV9TVE9SQUdFIiwiQUNDRVNTX0FORF9NQU5BR0VfQUlfTU9ERUxfSFVCIiwiQ1JFQVRFX05FVFdPUktfU0VDVVJJVFlfR1JPVVBTIiwiQUNDRVNTX0FORF9NQU5BR0VfSUFNX1JFU09VUkNFUyJdLCJ1dWlkIjoiZTBlZGEzMmMtYWYyZS00MTAzLWI2NTEtYzUxODFkNWI0NWUyIiwicmVzZWxsZXJJZCI6MSwicmVnRG9tYWluIjoiaW9ub3MuZGUifSwiZXhwIjoxNzQzMDc0ODE0fQ.djYpLyl8H5qlUsbd3q9CoPer34a6jrA6Csv0njFVXbLjWKhT2HefAFfakVlr4R3bthyMPTtSsEJkMDotKACCzMiFnSSon3y7i5C9SGTEDQOCQI1HLOGGV8C7x3b9rHfWsxt6QZ-00Qv7cHAuea7MkqqyhlaXKg1MGkZoBLauYv3E6pOTKA5I9ft-M_o7MPgKBgvPXdX4YS51XC7iVmDlo4bpeoh3La-DFRresdxcmXoExSSoaeFDmfSXQqlYgITjIpfc_uLl1i4dM7VgzNAu9HcdKGnMf_OYCYy8G0UqLdQ7xrF81whxd6HyN8sE4G1v-8b1yPzTcBs0cH8ZHjZbEQ"

# Dropdown options for the language
languages = ["German", "English", "French", "Spanish", "Italian"]


def create_story(number_of_children):
    # Generate story
    MODEL_NAME = "meta-llama/Meta-Llama-3.1-70B-Instruct"
    endpoint = "https://openai.inference.de-txl.ionos.com/v1/chat/completions"
    PROMPT = [
    {"role": "system", "content": "You are an author who creates beautiful bedtime stories for kids."},
    {"role": "user", "content": f"Generate a bedtime story that include {number_of_children}. Only give back the story itself in the translated language without any additional comments."}
    ]
    header = {
    "Authorization": f"Bearer {IONOS_API_TOKEN}", 
    "Content-Type": "application/json"
    }
    body = {
        "model": MODEL_NAME,
        "messages": PROMPT,
    }
    response = requests.post(endpoint, json=body, headers=header).json()
    return response['choices'][0]['message']['content']


def translate(story_english, to_language):
    MODEL_NAME = "meta-llama/Meta-Llama-3.1-70B-Instruct"
    endpoint = "https://openai.inference.de-txl.ionos.com/v1/chat/completions"
    PROMPT = [
    {"role": "system", "content": f"You are an bi-lingual assistant who creates translate from english into {to_language}."},
    {"role": "user", "content": f"Translate the following story into {to_language}:\n\n{story_english}"}
    ]
    header = {
    "Authorization": f"Bearer {IONOS_API_TOKEN}", 
    "Content-Type": "application/json"
    }
    body = {
        "model": MODEL_NAME,
        "messages": PROMPT,
    }
    response = requests.post(endpoint, json=body, headers=header).json()
    return response['choices'][0]['message']['content']


def create_image(story:str, language:str):
    MODEL_NAME = "black-forest-labs/FLUX.1-schnell"
    endpoint = "https://openai.inference.de-txl.ionos.com/v1/images/generations"
    PROMPT = f"A beautiful book cover with titles in {language} for the following story:\n\n{story}."
    header = {
        "Authorization": f"Bearer {IONOS_API_TOKEN}",
        "Content-Type": "application/json"
    }
    body = {
        "model": MODEL_NAME,
        "prompt": PROMPT,
        "size": "1024x1024"
    }
    response = requests.post(endpoint, json=body, headers=header)
    return response.json()['data'][0]['b64_json']  # Return only the base64 encoded string


def create_book(language, number_of_children):
    story = create_story(number_of_children)
    if not language == "English":
        story_output = translate(story, language)
    else:
        story_output = story
    image_response = create_image(story, language)

    # Decode the base64 image data
    img_data = b64decode(image_response)

    # Create a PIL image
    image_data_pil = Image.open(io.BytesIO(img_data))

    return story_output, image_data_pil


# Define Gradio interface
with gr.Blocks(theme=gr.themes.Glass(), title="BedTimeStories", css="footer{display:none !important}") as demo:
    gr.Markdown("# 🥱 BedTime Stories")
    gr.Markdown("## Everyday a new bedtime story for kids ")
    
    with gr.Row():
        language = gr.Dropdown(label="Select your language", choices=languages)
    with gr.Row():
        number_of_children = gr.Number(label="Number of children", value=1)
    
    create_button = gr.Button("Create")
    
    with gr.Row():
        image_output = gr.Image(type="pil")
        story_output = gr.Textbox(label="Story:")
    
    create_button.click(fn=create_book, inputs=[language, number_of_children], outputs=[story_output, image_output])

demo.launch()