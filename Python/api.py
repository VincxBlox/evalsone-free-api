import json
import os
import requests
import time
import sys
from flask import Flask, request, jsonify
import asyncio

# Configuration defaults
DEFAULT_CONFIG = {
    "auth_key": None,
    "log_file": "logs.txt",
    "verbose": False,
    "proxy": None,
    "logging_enabled": True,
    "port": 80,
    "sys_msg": "your an ai bru just work holy shit"
}


# Load configuration from `cfg.json` or create it if not found
def load_config():
    config_path = os.path.join(os.getcwd(), "cfg.json")
    if not os.path.exists(config_path):
        with open(config_path, "w") as config_file:
            json.dump(DEFAULT_CONFIG, config_file, indent=4)
        print(f"Configuration file 'cfg.json' not found. A default one has been created at {config_path}.")
        print("Please update the 'auth_key' field with your API key, or run the make acc script...")
        time.sleep(5)
        sys.exit(1)  # Exit after 5 seconds
    with open(config_path, "r") as config_file:
        config = json.load(config_file)
    return {**DEFAULT_CONFIG, **config}  # Merge defaults with user config

config = load_config()

EVALSONE_API_KEY = config.get("auth_key")
if not EVALSONE_API_KEY or EVALSONE_API_KEY == DEFAULT_CONFIG["auth_key"]:
    print("Error: Missing or invalid 'auth_key' in configuration file 'cfg.json'. Please update it.")
    sys.exit(1)
EVALSONE_API_URL = "https://api.evalsone.com/api/llm/chatcomplete"
EVALSONE_API_TEST_URL = "https://api.evalsone.com/api/llm"
LOG_FILE = config.get("log_file", "logs.txt")
VERBOSE = config.get("verbose", False)
PROXY = config.get("proxy", None)
LOGGING_ENABLED = config.get("logging_enabled", True)
system_message = config.get("sys_msg", "You are an AI assistant")  # Default to the default message if not specified in the config
PORT = config.get("port", 8080)

# Check for runtime arguments
if "--verbose" in sys.argv:
    VERBOSE = True
if "--no-logs" in sys.argv:
    LOGGING_ENABLED = False
if "--proxy" in sys.argv:
    try:
        PROXY = sys.argv[sys.argv.index("--proxy") + 1]
    except IndexError:
        raise ValueError("Proxy URL must be specified after '--proxy'.")

# Logger utility
def log_message(message, level="info"):
    """
    Log messages to both console and log file.

    Levels:
    - "info": General information (always shown in non-verbose mode).
    - "debug": Detailed debugging info (only shown in verbose mode).
    - "error": Errors (always shown).
    """
    timestamp = time.strftime("[%Y-%m-%d %H:%M:%S]")
    log_entry = f"{timestamp} [{level.upper()}] {message}\n"

    # Always log errors and general info, but only log debug info if VERBOSE is enabled
    if level in ["info", "error"] or VERBOSE and level == "debug":
        print(log_entry.strip())  # Output to console

    if LOGGING_ENABLED:
        with open(LOG_FILE, "a") as log_file:
            log_file.write(log_entry)

def send_evalsone_request(messages, system_message, model_id=726, raw=False, max_tokens=2048):
    payload = {
        "messages": [{"role": "system", "content": system_message}, *messages],
        "model_id": model_id,
        "max_tokens": max_tokens,
        "top_p": 1,
        "stream": True,
        "toolCalls": False,
        "tool_choice": "auto",
        "auto_invoke": 0,
        "save_cost": 0,
        "artifact_mode": 0,
        "functions": [],
        "mcps": []
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:135.0) Gecko/20100101 Firefox/135.0",
        "Accept": "*/*",
        "Content-Type": "application/json",
        "Blade-auth": EVALSONE_API_KEY
    }

    proxies = {"http": PROXY, "https": PROXY} if PROXY else None
    log_message(f"Sending request to Evalsone API.", level="info")
    log_message(f"Payload: {json.dumps(payload)}", level="debug")

    try:
        response = requests.post(
            EVALSONE_API_URL,
            headers=headers,
            json=payload,
            stream=True,
            proxies=proxies
        )
        response.raise_for_status()

        content_chunks = []
        model_info = {}
        for line in response.iter_lines(decode_unicode=True):
            if line:
                if not line.startswith("data: "):
                    continue
                line = line[6:]
                if '[DONE]' in line or line.strip().startswith("DONE"):
                    continue
                try:
                    chunk_data = json.loads(line)
                    if not model_info and "model" in chunk_data:
                        model_info = {
                            "model": chunk_data["model"],
                            "object": chunk_data.get("object", "chat.completion"),
                            "created": chunk_data.get("created", int(time.time()))
                        }
                    if "choices" in chunk_data and len(chunk_data["choices"]) > 0:
                        delta = chunk_data["choices"][0].get("delta", {})
                        if "content" in delta:
                            raw_content = delta["content"]
                            content_chunks.append(raw_content if raw else sanitize_content(raw_content))
                            if VERBOSE:
                                log_message(f"Chunk: {raw_content}", level="debug")
                except json.JSONDecodeError as e:
                    log_message(f"Error decoding JSON: {e}", level="error")
                    content_chunks.append(line)

        raw_content = "".join(content_chunks)
        final_content = sanitize_content(raw_content)
        log_message("Response received from Evalsone API.", level="info")
        if VERBOSE:
            log_message(f"Final response content: {final_content}", level="debug")

        return {
            "content": final_content,
            "model": model_info.get("model", ""),
            "object": model_info.get("object", "chat.completion"),
            "created": model_info.get("created", int(time.time()))
        }

    except requests.RequestException as e:
        log_message(f"Request failed: {e}", level="error")
        return None

# Check connection to the proxy (if configured)
def check_proxy():
    if PROXY:
        try:
            response = requests.get("http://icanhazip.com", proxies={"http": PROXY, "https": PROXY}, timeout=5)
            if response.status_code == 200:
                log_message(f"Proxy connection successful. IP: {response.text.strip()}", level="info")
                return True
            else:
                log_message("Error: Proxy returned non-200 status code.", level="error")
                return False
        except requests.RequestException as e:
            log_message(f"Error connecting to proxy: {e}", level="error")
            return False
    else:
        log_message("No proxy configured.", level="info")
        return True  # No proxy is fine

# Check connection to the Evalsone API
def check_evalsone_api():
    try:
        response = requests.get(EVALSONE_API_TEST_URL, timeout=5)
        if response.status_code == 200:
            log_message("Evalsone API connection successful.", level="info")
            return True
        else:
            log_message(f"Error: Evalsone API returned non-200 status code: {response.status_code}", level="error")
            return False
    except requests.RequestException as e:
        log_message(f"Error connecting to Evalsone API: {e}", level="error")
        return False

import re

def sanitize_content(content: str) -> str:
    """
    Sanitize the content by:
    - Removing newline characters (`\n`).
    - Replacing escaped double quotes (`\"`) with regular double quotes (`"`).
    
    Args:
    - content (str): The raw content to be sanitized.

    Returns:
    - str: The sanitized content.
    """
    # First, replace escaped quotes with regular quotes
    content = content.replace('\\"', '"')

    # Then remove newline characters
    content = content.replace('\n', '')
    
    return content


# Initialize Flask app
app = Flask(__name__)

@app.route("/v1/chat/completions", methods=["POST"])
def chat_completions():
    content_length = request.content_length
    post_data = request.get_data()  # No 'await' here

    try:
        # Check the proxy (only if it's specified)
        if not check_proxy():
            return jsonify({"error": "Proxy connection failed"}), 500

        if not check_evalsone_api():
            return jsonify({"error": "Evalsone API connection failed"}), 500

        data = json.loads(post_data)
        messages = data.get("messages", [])
        model = data.get("model", None)
        max_tokens = data.get("max_tokens", 2048)  # Default max tokens
        raw = data.get("raw", False)  # Raw output toggle

        model_id_mapping = {
            "gpt-4o-mini": 620,
            "gemini-2.0-flash": 740,
            "claude-3.5-haiku": 726,
            "gemini-1.5-flash": 641,
            "claude-2": 725,
            "claude-3": 726
        }
        model_id = model_id_mapping.get(model, 726)  # Default to 726 if model is unknown

        result = send_evalsone_request(messages, system_message, model_id, raw, max_tokens)

        if result:
            return jsonify({
                "id": str(int(time.time())),
                "object": result.get("object", ""),
                "created": result.get("created", int(time.time())),
                "model": result.get("model", ""),
                "choices": [{"message": {"role": "assistant", "content": result.get("content", "")}}]
            })
        else:
            return jsonify({"error": "Failed to get response from Evalsone API."}), 500

    except Exception as e:
        log_message(f"Error processing request: {e}", level="error")
        return jsonify({"error": f"Error: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=PORT)
    print(f"free api project STARTED on port {port}.")
