import gradio as gr
from openai import OpenAI
import os
import httpx
import asyncio
import json

# It's recommended to set the API key as an environment variable for security.
# If the environment variable is not set, you will be prompted to enter it in the UI.
API_KEY_FILE = ".api_key"
INSTRUCTION_FILE = ".instruction_text"
PROMPT_TEMPLATE_FILE = ".prompt_template"
SYSTEM_PROMPT_FILE = ".system_prompt"
CACHE_FILE = "generation_cache.json"

def load_cache():
    """Loads the generation history from a JSON file."""
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            # If the file is corrupted or empty, start fresh
            return []
    return []

def save_cache(data):
    """Saves the generation history to a JSON file."""
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


api_key = os.environ.get("DEEPSEEK_API_KEY")
if not api_key and os.path.exists(API_KEY_FILE):
    with open(API_KEY_FILE, "r") as f:
        api_key = f.read().strip()

DEFAULT_INSTRUCTIONS = "Enter a word to generate a sentence. Click any word in the result to generate a new sentence with that word."
instruction_text = DEFAULT_INSTRUCTIONS
if os.path.exists(INSTRUCTION_FILE):
    with open(INSTRUCTION_FILE, "r", encoding="utf-8") as f:
        instruction_text = f.read().strip()

DEFAULT_PROMPT_TEMPLATE = """
For the word "{word}", provide the following in a JSON format:
1. A simple English sentence using the word.
2. The International Phonetic Alphabet (IPA) transcription.
3. A list of its Chinese translations, including part of speech and definition.

Example JSON format for the word "book":
{{
  "sentence": "I need to book a flight to Beijing.",
  "phonetics": "/bʊk/",
  "translations": [
    {{
      "partOfSpeech": "n.",
      "definition": "书, 书籍; 卷, 册"
    }},
    {{
      "partOfSpeech": "v.",
      "definition": "预订, 预约"
    }}
  ]
}}
"""
prompt_template = DEFAULT_PROMPT_TEMPLATE
if os.path.exists(PROMPT_TEMPLATE_FILE):
    with open(PROMPT_TEMPLATE_FILE, "r", encoding="utf-8") as f:
        prompt_template = f.read().strip()

DEFAULT_SYSTEM_PROMPT = "You are a helpful assistant that provides sentence examples, phonetics, and detailed translations with parts of speech in a JSON format. Use common abbreviations for parts of speech (e.g., n., v., adj.)."
system_prompt = DEFAULT_SYSTEM_PROMPT
if os.path.exists(SYSTEM_PROMPT_FILE):
    with open(SYSTEM_PROMPT_FILE, "r", encoding="utf-8") as f:
        system_prompt = f.read().strip()

client = None

AUDIO_OUTPUT_DIR = "generated_audio"

def generate_audio_url(text, pronunciation='us'):
    """生成有道发音API的音频URL，支持单词或句子"""
    base_url = 'https://dict.youdao.com/dictvoice?audio='
    if pronunciation == 'uk':
        return f"{base_url}{text}&type=1"
    elif pronunciation == 'us':
        return f"{base_url}{text}&type=2"
    else:
        return None

async def get_audio_file(text, pronunciation='us'):
    """获取音频文件，优先从本地缓存读取，否则从API下载。"""
    sanitized_text = "".join(c for c in text if c.isalnum() or c in " .-_").rstrip()
    audio_filename = f"{sanitized_text}_{pronunciation}.mp3"
    audio_path = os.path.join(AUDIO_OUTPUT_DIR, audio_filename)

    if os.path.exists(audio_path):
        return audio_path

    os.makedirs(AUDIO_OUTPUT_DIR, exist_ok=True)
    url = generate_audio_url(text, pronunciation)
    if not url:
        return None

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            if response.status_code == 200 and 'audio' in response.headers.get('Content-Type', ''):
                with open(audio_path, 'wb') as f:
                    f.write(response.content)
                return audio_path
            else:
                return None
    except Exception as e:
        print(f"Error fetching audio for '{text}': {e}")
        return None

def save_instruction_text(text_to_save):
    """Saves the instruction text to a file and returns it."""
    global instruction_text
    if text_to_save:
        with open(INSTRUCTION_FILE, "w", encoding="utf-8") as f:
            f.write(text_to_save)
        instruction_text = text_to_save
        return text_to_save
    # Do not change the instruction if the input is empty
    return instruction_text

def save_prompt_template(template_to_save):
    """Saves the prompt template to a file and returns it."""
    global prompt_template
    if template_to_save:
        with open(PROMPT_TEMPLATE_FILE, "w", encoding="utf-8") as f:
            f.write(template_to_save)
        prompt_template = template_to_save
        return template_to_save
    return prompt_template

def save_system_prompt(prompt_to_save):
    """Saves the system prompt to a file and returns it."""
    global system_prompt
    if prompt_to_save:
        with open(SYSTEM_PROMPT_FILE, "w", encoding="utf-8") as f:
            f.write(prompt_to_save)
        system_prompt = prompt_to_save
        return prompt_to_save
    return system_prompt

def save_api_key(key_to_save):
    """Saves the API key to a file and updates the global variable."""
    if key_to_save:
        with open(API_KEY_FILE, "w") as f:
            f.write(key_to_save)
        global api_key
        api_key = key_to_save
        return "<p style='color: green;'>API key saved successfully!</p>"
    return "<p style='color: orange;'>API key cannot be empty.</p>"

async def generate_sentence_and_translation(word, current_api_key, base_url, custom_prompt_template, custom_system_prompt):
    """
    Generates a sentence, translation, phonetics, and audio for the input word.
    """
    key_to_use = current_api_key or api_key
    if not key_to_use:
        return "Error: Please enter or save your DeepSeek API key below.", [], "", None
    if not word:
        return "Please enter a word.", [], "", None

    try:
        client = OpenAI(api_key=key_to_use, base_url=base_url)
        prompt = custom_prompt_template.format(word=word)
        response = await asyncio.to_thread(
            client.chat.completions.create,
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": custom_system_prompt},
                {"role": "user", "content": prompt},
            ],
            stream=False,
            response_format={"type": "json_object"}
        )
        
        content = response.choices[0].message.content
        data = json.loads(content)
        
        sentence = data.get("sentence", "No sentence generated.")
        phonetics = data.get("phonetics", "No phonetics found.")
        translations = data.get("translations", [])
        
        words = sentence.split()
        
        translation_details = []
        if translations:
            for t in translations:
                pos = t.get('partOfSpeech', '')
                definition = t.get('definition', '')
                if pos and definition:
                    translation_details.append(f"**{pos}** {definition}")
        
        translation_text = f"**音标:** {phonetics}\n\n" + "\n".join(translation_details)
        if not translation_details:
            translation_text = f"**音标:** {phonetics}\n\nNo translation found."

        # Asynchronously fetch the audio file for the input word
        audio_path = await get_audio_file(word)
        
        return sentence, words, translation_text, audio_path

    except Exception as e:
        error_message = f"An error occurred: {e}"
        if "Incorrect API key" in str(e):
            error_message = "Error: The provided API key is incorrect."
        elif isinstance(e, json.JSONDecodeError):
            error_message = "Error: Failed to parse the response from the API. The API may not have returned valid JSON."
        return error_message, [], "", None

def clean_word(word):
    """Removes common trailing punctuation from a word."""
    return word.strip(".,!?;:'\"- ")

def update_ui_with_buttons(sentence, words):
    """
    Updates the UI to display the sentence and creates clickable buttons for each word.
    """
    buttons = [gr.update(value=word, visible=True) for word in words]
    max_buttons = 20 
    for _ in range(len(words), max_buttons):
        buttons.append(gr.update(visible=False))
    
    # The first element of the returned list is the sentence string.
    # The rest are the button update objects.
    return [sentence] + buttons

async def generate_and_update_history(word, current_api_key, base_url, custom_prompt_template, custom_system_prompt, history, index):
    """
    Generates content if not in cache, updates history, and returns all UI updates including audio.
    """
    if not word:
        num_outputs = 8 + 20
        return tuple([gr.update()] * num_outputs)

    word = clean_word(word)

    # First, search for the word in the entire history without modifying it.
    found_index = -1
    for i, entry in enumerate(history):
        if entry["word"] == word:
            found_index = i
            break

    if found_index != -1:
        # Word exists in history, just update the index to point to it.
        index = found_index
    else:
        # Word is new, so it will be added to the end of the history cache.
        # Generate new content since it's not in the cache.
        sentence, words, translation_text, audio_path = await generate_sentence_and_translation(word, current_api_key, base_url, custom_prompt_template, custom_system_prompt)

        if not isinstance(words, list) or not words:
            button_updates = update_ui_with_buttons(sentence, [])
            prev_btn = gr.update(interactive=index > 0)
            next_btn = gr.update(interactive=index < len(history) - 1)
            return (word, sentence, "", None, history, index, prev_btn, next_btn, *button_updates[1:])

        new_entry = {
            "word": word,
            "sentence": sentence,
            "words": words,
            "translation_text": translation_text,
            "audio_path": audio_path
        }
        history.append(new_entry)
        save_cache(history)  # Save the updated history to the cache
        index = len(history) - 1

    # Display the content from the correct entry (either newly generated or found in history).
    current_entry = history[index]
    
    button_updates = update_ui_with_buttons(current_entry["sentence"], current_entry["words"])
    prev_btn_update = gr.update(interactive=index > 0)
    next_btn_update = gr.update(interactive=index < len(history) - 1)
    
    audio_update = gr.update(value=current_entry.get("audio_path"), autoplay=True)

    return (
        current_entry["word"],
        button_updates[0],
        current_entry["translation_text"],
        audio_update,
        history,
        index,
        prev_btn_update,
        next_btn_update,
        *button_updates[1:]
    )

async def regenerate_and_update_history(word, current_api_key, base_url, custom_prompt_template, custom_system_prompt, history, index):
    """
    Forces regeneration of content for a word, updates the cache, and updates the UI.
    """
    if not word:
        num_outputs = 8 + 20
        return tuple([gr.update()] * num_outputs)

    word = clean_word(word)

    # Always generate new content, bypassing the cache check.
    sentence, words, translation_text, audio_path = await generate_sentence_and_translation(word, current_api_key, base_url, custom_prompt_template, custom_system_prompt)

    if not isinstance(words, list) or not words:
        button_updates = update_ui_with_buttons(sentence, [])
        # On error, keep the history state as is, but update buttons based on current index
        prev_btn = gr.update(interactive=index > 0)
        next_btn = gr.update(interactive=index < len(history) - 1 if history else False)
        return (word, sentence, "", None, history, index, prev_btn, next_btn, *button_updates[1:])

    new_entry = {
        "word": word,
        "sentence": sentence,
        "words": words,
        "translation_text": translation_text,
        "audio_path": audio_path
    }

    # Find if the word exists to update it, otherwise append.
    found_index = -1
    for i, entry in enumerate(history):
        if entry["word"] == word:
            found_index = i
            break

    if found_index != -1:
        history[found_index] = new_entry
        index = found_index
    else:
        history.append(new_entry)
        index = len(history) - 1

    save_cache(history)

    # Display the updated content
    current_entry = history[index]
    button_updates = update_ui_with_buttons(current_entry["sentence"], current_entry["words"])
    prev_btn_update = gr.update(interactive=index > 0)
    next_btn_update = gr.update(interactive=index < len(history) - 1)
    audio_update = gr.update(value=current_entry.get("audio_path"), autoplay=True)

    return (
        current_entry["word"],
        button_updates[0],
        current_entry["translation_text"],
        audio_update,
        history,
        index,
        prev_btn_update,
        next_btn_update,
        *button_updates[1:]
    )

def navigate_history(history, index, direction):
    """
    Moves back or forward in the history and displays the cached content including audio.
    """
    new_index = index + direction
    
    if not (0 <= new_index < len(history)):
        # Match the number of outputs from the main generation function
        num_outputs = 8 + 20 
        return tuple([gr.update()] * num_outputs)

    entry = history[new_index]
    
    button_updates = update_ui_with_buttons(entry["sentence"], entry["words"])
    prev_btn_update = gr.update(interactive=new_index > 0)
    next_btn_update = gr.update(interactive=new_index < len(history) - 1)
    
    audio_update = gr.update(value=entry.get("audio_path"), autoplay=True)

    return (
        entry["word"],
        button_updates[0],
        entry["translation_text"],
        audio_update,
        history,
        new_index,
        prev_btn_update,
        next_btn_update,
        *button_updates[1:]
    )

# Gradio Interface
custom_css = """
#generated_sentence_output textarea {
    font-size: 24px !important;
    line-height: 1.5 !important;
}
"""
with gr.Blocks(css=custom_css) as demo:
    gr.Markdown("# 发散式思维造句记忆单词Interactive Sentence Generator")
    instruction_markdown = gr.Markdown(instruction_text)
    
    # Add state components to store history, initialized from cache
    history_state = gr.State(load_cache())
    history_index_state = gr.State(-1)

    with gr.Row():
        word_input = gr.Textbox(label="Enter a word", placeholder="e.g., beautiful")
        with gr.Column():
            generate_button = gr.Button("Generate")
            regenerate_button = gr.Button("Regenerate")

    with gr.Row():
        prev_button = gr.Button("Previous Word", interactive=False)
        next_button = gr.Button("Next Word", interactive=False)

    sentence_output = gr.Textbox(label="Generated Sentence", interactive=False, elem_id="generated_sentence_output")
    translation_output = gr.Markdown(label="Word Details")
    audio_output = gr.Audio(label="Sentence Audio", autoplay=False)
    
    with gr.Row() as button_row:
        max_buttons = 20
        word_buttons = [gr.Button(visible=False) for _ in range(max_buttons)]

    with gr.Accordion("UI Settings", open=False):
        instruction_input = gr.Textbox(
            label="Instruction Text",
            value=instruction_text,
            lines=3,
            placeholder="Enter the instruction text to display on the main screen."
        )
        save_instruction_button = gr.Button("Save Instructions")
        prompt_template_input = gr.Textbox(
            label="Prompt Template",
            value=prompt_template,
            lines=10,
            placeholder="Enter the prompt template. Use {word} as a placeholder for the input word."
        )
        save_prompt_button = gr.Button("Save Prompt Template")
        system_prompt_input = gr.Textbox(
            label="System Prompt",
            value=system_prompt,
            lines=5,
            placeholder="Enter the system prompt for the AI model."
        )
        save_system_prompt_button = gr.Button("Save System Prompt")

    with gr.Accordion("API Settings", open=False):
        base_url_input = gr.Textbox(
            label="DeepSeek API Base URL", 
            value="https://api.deepseek.com"
        )
        api_key_input = gr.Textbox(
            label="DeepSeek API Key", 
            placeholder="Enter your DeepSeek API key here",
            value=api_key or "",
            type="password"
        )
        with gr.Row():
            save_api_key_button = gr.Button("Save API Key")
            api_status_message = gr.HTML()

    # --- Event Handlers ---

    # Handler for saving instructions
    save_instruction_button.click(
        fn=save_instruction_text,
        inputs=[instruction_input],
        outputs=[instruction_markdown]
    )

    save_prompt_button.click(
        fn=save_prompt_template,
        inputs=[prompt_template_input],
        outputs=[prompt_template_input]
    )

    save_system_prompt_button.click(
        fn=save_system_prompt,
        inputs=[system_prompt_input],
        outputs=[system_prompt_input]
    )

    # Handler for the save button
    save_api_key_button.click(
        fn=save_api_key,
        inputs=[api_key_input],
        outputs=[api_status_message]
    )

    # Main generation logic
    generate_button.click(
        fn=generate_and_update_history,
        inputs=[word_input, api_key_input, base_url_input, prompt_template_input, system_prompt_input, history_state, history_index_state],
        outputs=[word_input, sentence_output, translation_output, audio_output, history_state, history_index_state, prev_button, next_button] + word_buttons
    )
    word_input.submit(
        fn=generate_and_update_history,
        inputs=[word_input, api_key_input, base_url_input, prompt_template_input, system_prompt_input, history_state, history_index_state],
        outputs=[word_input, sentence_output, translation_output, audio_output, history_state, history_index_state, prev_button, next_button] + word_buttons
    )

    regenerate_button.click(
        fn=regenerate_and_update_history,
        inputs=[word_input, api_key_input, base_url_input, prompt_template_input, system_prompt_input, history_state, history_index_state],
        outputs=[word_input, sentence_output, translation_output, audio_output, history_state, history_index_state, prev_button, next_button] + word_buttons
    )

    # Logic for history navigation buttons
    prev_button.click(
        fn=navigate_history,
        inputs=[history_state, history_index_state, gr.State(-1)],
        outputs=[word_input, sentence_output, translation_output, audio_output, history_state, history_index_state, prev_button, next_button] + word_buttons
    )
    next_button.click(
        fn=navigate_history,
        inputs=[history_state, history_index_state, gr.State(1)],
        outputs=[word_input, sentence_output, translation_output, audio_output, history_state, history_index_state, prev_button, next_button] + word_buttons
    )

    # Logic for each word button: auto-fill the input box and generate a new sentence
    for button in word_buttons:
        button.click(
            fn=generate_and_update_history,
            inputs=[button, api_key_input, base_url_input, prompt_template_input, system_prompt_input, history_state, history_index_state],
            outputs=[word_input, sentence_output, translation_output, audio_output, history_state, history_index_state, prev_button, next_button] + word_buttons
        )

if __name__ == "__main__":
    demo.launch()
