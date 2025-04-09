from base64 import b64decode
from PIL import Image
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import deepl
import gradio as gr
import io
import os
import requests


# Global Stuff
durations = ["5 min", "10 min", "more than 10 min"]
amount_children = ["1", "2", "3", "more than 3"]
ages = ["3 years and older", "5 years and older", "7 years and older"]
languages = ["English", "French", "German", "Italian", "Spanish"]
targets = ["Girls", "Boys", "Girls and Boys"]
themes = ["Dinosaurs", "Fairies", "Firebrigade", "Friendship", "Magic", "Pirates", "Ponys", "Princesses", "Police", "Space", "Superheroes"]
IONOS_API_TOKEN = os.getenv('IONOS_API_TOKEN')
deepl_auth_key = os.getenv('deepl_auth_key')


def create_story(number_of_children, target, theme, target_age, duration):
    # Generate story
    MODEL_NAME = "meta-llama/Meta-Llama-3.1-405B-Instruct-FP8"
    endpoint = "https://openai.inference.de-txl.ionos.com/v1/chat/completions"
    PROMPT = [
    {"role": "system", "content": "You are an author who creates beautiful bedtime stories for kids."},
    {"role": "user", "content": f"Generate a beautiful bedtime story for {target} about {theme}. The audience contains {number_of_children} kids in the age of {target_age}. The story should take about {duration} to read assuming an average speed of 183 words per minute. Avoid any additional comments besides the actual story. Do not use too long sentences, the story shall be easy to read and understandable for children."}
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


def create_book(language, target, theme, number_of_children, target_age, duration):
    story = create_story(number_of_children, target, theme, target_age, duration)
    if not "English" in language:
        deepl_client = deepl.DeepLClient(deepl_auth_key)
        usage = deepl_client.get_usage()
        if usage.any_limit_reached:
            story_output = translate(story, language)
        else:
            match language:
                case "French":
                    target_lang = "FR"
                case "German":
                    target_lang = "DE"
                case "Italian":
                    target_lang = "IT"
                case "Spanish":
                    target_lang = "ES"
            story_output = deepl_client.translate_text(story, target_lang=target_lang)    
    else:
        story_output = story
    image_response = create_image(story)
    # Decode the base64 image data
    img_data = b64decode(image_response)
    # Create a PIL image
    image_data_pil = Image.open(io.BytesIO(img_data))    
    return story_output, image_data_pil


def download_as_pdf(story, image):
    # Create a PDF file
    pdf_path = "story.pdf"
    c = canvas.Canvas(pdf_path, pagesize=A4)    
    # A4 dimensions in points (595.2, 841.8)
    page_width = A4[0]
    page_height = A4[1]    
    # Set image width to 80% of page width and maintain aspect ratio
    image_width = page_width * 0.8
    image_height = image_width  # Since it's a square image    
    # Add disclaimer at the top
    disclaimer = "AI Generated Story from https://stories.brose-engineering.de"
    c.setFont("Helvetica", 10)  # Smaller font for disclaimer
    disclaimer_width = c.stringWidth(disclaimer, "Helvetica", 10)
    disclaimer_x = (page_width - disclaimer_width) / 2
    disclaimer_y = page_height - 30  # Position at top with margin
    c.drawString(disclaimer_x, disclaimer_y, disclaimer)
    # Position image at top of page with some margin
    margin_top = 50
    image_x = (page_width - image_width) / 2
    image_y = page_height - margin_top - image_height    
    # Add the image to the PDF (only on first page)
    c.drawInlineImage(image, image_x, image_y, width=image_width, height=image_height)    
    # Text parameters
    text_margin_top = 30
    text_width = page_width * 0.9  # 90% of page width
    text_x = (page_width - text_width) / 2
    text_y = image_y - text_margin_top
    line_height = 20
    margin_bottom = 50    
    # Split story into words
    words = story.split()
    current_line = []    
    c.setFont("Helvetica", 12)    
    # Process words and create lines
    for word in words:
        current_line.append(word)
        line_width = c.stringWidth(' '.join(current_line), "Helvetica", 12)        
        if line_width > text_width:
            current_line.pop()
            # Draw the line
            if text_y < margin_bottom:  # Need new page
                c.showPage()  # Start new page
                text_y = page_height - margin_top  # Reset Y position for new page
                c.setFont("Helvetica", 12)  # Need to reset font after new page            
            c.drawString(text_x, text_y, ' '.join(current_line))
            text_y -= line_height
            current_line = [word]    
    # Draw remaining text
    if current_line:
        if text_y < margin_bottom:  # Need new page
            c.showPage()  # Start new page
            text_y = page_height - margin_top
            c.setFont("Helvetica", 12)        
        c.drawString(text_x, text_y, ' '.join(current_line))    
    # Save the PDF
    c.save()    
    return pdf_path


# Define Gradio interface
with gr.Blocks(theme=gr.themes.Glass(), title="BedTimeStories", css="footer{display:none !important}") as demo:
    gr.Markdown("# 🥱 BedTime Stories")
    gr.Markdown("### Daily a new bedtime story for kids. It just takes a minute.")
    gr.Markdown("### Available for many languages spoken in the EU. 🇪🇺")
    
    with gr.Row():
        number_of_children = gr.Dropdown(label="Number of children: 🥱😌😴", choices=amount_children)
        language = gr.Dropdown(label="Select your language: 🇬🇧 🇫🇷 🇩🇪 🇮🇹 🇪🇦", choices=languages)
        target_age = gr.Dropdown(label="Childrens age: 3️⃣4️⃣5️⃣", choices=ages)
    with gr.Row():
        duration = gr.Dropdown(label="Story length: ⏳", choices=durations)
        target = gr.Dropdown(label="Story for: ♀️♂️", choices=targets)
        theme = gr.Dropdown(label="Story about: 📖", choices=themes)
    create_button = gr.Button("Create Story")
    with gr.Row():
        image_output = gr.Image(type="pil", interactive=False, show_label=False)
    with gr.Row():
        story_output = gr.Textbox(label="Story:", interactive=False, lines=25)

    download_story_button = gr.Button("Download Story", interactive=True)
    create_button.click(fn=create_book, inputs=[language, target, theme, number_of_children, target_age, duration], outputs=[story_output, image_output], concurrency_limit=3)
    download_story_button.click(fn=download_as_pdf, inputs=[story_output, image_output], outputs=gr.File(label="Your story as PDF", interactive=False))

    gr.Markdown("Made with ❤️ in 🇩🇪 | [brose-engineering.de](https://brose-engineering.de/) | [GitHub](https://github.com/brose-engineering/bedtime_stories)")
    gr.Markdown("Translations by DeepL | [deepl.com](https://www.deepl.com) | [Why DeepL?](https://www.deepl.com/en/quality)")
    gr.Markdown("This Gradio-App is hosted on Huggingface | [Huggingface Terms of Service](https://huggingface.co/terms-of-service) | [Gradio.app](https://www.gradio.app/)")

demo.launch()
