from base64 import b64decode
from PIL import Image
import gradio as gr
import os
import io
import requests


# Global Stuff
languages = ["English", "French", "German", "Italian", "Polish", "Portuguese" , "Spanish"]
targets = ["Girls", "Boys", "Girls and Boys"]
themes = ["Friendship", "Dinosaurs", "Police", "Firebrigade", "Action-Heros", "Princesses", "Pets", "Ponys"] 
IONOS_API_TOKEN = os.getenv('IONOS_API_TOKEN')


def create_story(number_of_children, target, theme):
    # Generate story
    MODEL_NAME = "meta-llama/Meta-Llama-3.1-405B-Instruct-FP8"
    endpoint = "https://openai.inference.de-txl.ionos.com/v1/chat/completions"
    PROMPT = [
    {"role": "system", "content": "You are an author who creates beautiful bedtime stories for kids."},
    {"role": "user", "content": f"Generate a beautiful bedtime story for {target} about {theme}. There is an audience of {number_of_children} kids. Create only a story without any additional comments."}
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
    MODEL_NAME = "meta-llama/Meta-Llama-3.1-405B-Instruct-FP8"
    endpoint = "https://openai.inference.de-txl.ionos.com/v1/chat/completions"
    PROMPT = [
    {"role": "system", "content": f"You are an assistant who translates text from English into different languages."},
    {"role": "user", "content": f"Carefully translate the following story into {to_language}. Take care about grammar and correct spelling. Create only the translated story without any additional comments:\n\n{story_english}"}
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


def create_image(story:str):
    MODEL_NAME = "black-forest-labs/FLUX.1-schnell"
    endpoint = "https://openai.inference.de-txl.ionos.com/v1/images/generations"
    PROMPT = f"A beautiful book cover without any titles for the following story:\n\n{story}."
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


def create_book(language, target, theme, number_of_children):
    story = create_story(number_of_children, target, theme)
    if not language == "English":
        story_output = translate(story, language)
    else:
        story_output = story
    image_response = create_image(story)

    # Decode the base64 image data
    img_data = b64decode(image_response)

    # Create a PIL image
    image_data_pil = Image.open(io.BytesIO(img_data))

    return story_output, image_data_pil


# Define Gradio interface
with gr.Blocks(theme=gr.themes.Glass(), title="BedTimeStories", css="footer{display:none !important}") as demo:
    gr.Markdown("# 🥱 BedTime Stories")
    gr.Markdown("### Daily a new bedtime story for kids. It just takes a minute.")
    gr.Markdown("### Available for a lot of languages spoken in the EU. 🇪🇺")
    
    with gr.Row():
        language = gr.Dropdown(label="Select your language:", choices=languages)
        number_of_children = gr.Number(label="Number of children", value=1)
    with gr.Row():
        target = gr.Dropdown(label="Story for:", choices=targets)
        theme = gr.Dropdown(label="Story about:", choices=themes)
    
    create_button = gr.Button("Create")
    
    with gr.Row():
        image_output = gr.Image(type="pil")
    with gr.Row():
        story_output = gr.Textbox(label="Story:", lines=30)

    gr.Markdown("Made with ❤️ in Germany")
    
    create_button.click(fn=create_book, inputs=[language, target, theme, number_of_children], outputs=[story_output, image_output], concurrency_limit=3)

demo.launch(server_name="0.0.0.0", server_port=7860, favicon_path="favico.png")