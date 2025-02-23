import json
import os
import requests
import time
import base64
import argparse
from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS
import re

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Constants
LOG_FILE = "logs.txt"
models_data = []
tokens_data = {}

def parse_args():
    parser = argparse.ArgumentParser(description='API Server')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    parser.add_argument('--proxy', help='Proxy URL')
    parser.add_argument('--disable-log', action='store_true', help='Disable logging to file')
    parser.add_argument('--port', type=int, default=None, help='Port to run the server on')
    return parser.parse_args()

def log_message(message, level="info", args=None):
    """
    Log messages to both console and log file.
    """
    if args is None:
        args = parse_args()  # Only parse args if not already passed in
    
    timestamp = time.strftime("[%Y-%m-%d %H:%M:%S]")
    log_entry = f"{timestamp} [{level.upper()}] {message}\n"

    # Always log errors and general info, but only log debug info if verbose is enabled
    if level in ["info", "error"] or (args.verbose and level == "debug"):
        print(log_entry.strip())  # Output to console

    if not args.disable_log:
        with open(LOG_FILE, "a") as log_file:
            log_file.write(log_entry)



def load_models():
    """Load model mappings from models.json"""
    global models_data
    try:
        with open('models.json', 'r') as f:
            models = json.load(f)
            log_message(f"Loaded {len(models)} models from models.json", "info")
            models_data = models
    except FileNotFoundError:
        log_message("models.json not found. Creating empty models list.", "error")
        return []
    except json.JSONDecodeError as e:
        log_message(f"Error parsing models.json: {e}", "error")
        return []

def save_tokens(tokens_data):
    """Save tokens to tokens.json"""
    try:
        with open('tokens.json', 'w') as f:
            json.dump(tokens_data, f, indent=4)
        log_message("Successfully updated tokens.json", "debug")
    except Exception as e:
        log_message(f"Error saving tokens: {e}", "error")

def load_tokens():
    """Load tokens from tokens.json"""
    global tokens_data
    try:
        with open('tokens.json', 'r') as f:
            tokens_data = json.load(f)
            log_message("Successfully loaded tokens.json", "debug")
    except FileNotFoundError:
        log_message("tokens.json not found. Creating new tokens file.", "info")
    except json.JSONDecodeError as e:
        log_message(f"Error parsing tokens.json: {e}", "error")

def decode_auth_token(auth_token):
    """Decode base64 auth token to get email and password"""
    try:
        if not auth_token.startswith('Bearer '):
            log_message("Invalid authorization header format", "error")
            return None, None
            
        decoded = base64.b64decode(auth_token.split(' ')[1]).decode('utf-8')
        credentials = json.loads(decoded)
        
        email = credentials.get('email')
        password = credentials.get('password')
        
        if not email or not password:
            log_message("Missing email or password in credentials", "error")
            return None, None
            
        log_message(f"Successfully decoded credentials for {email}", "debug")
        return email, password
    except Exception as e:
        log_message(f"Error decoding auth token: {e}", "error")
        return None, None

def get_new_token(email, password, args=None):
    """Get new access token from Evalsone API"""
    login_url = "https://api.evalsone.com/api/user/login"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:136.0) Gecko/20100101 Firefox/136.0",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,fr;q=0.8,fr-FR;q=0.5,en;q=0.3",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Content-Type": "application/json;charset=utf-8",
        "Origin": "https://consolex.ai",
        "DNT": "1",
        "Sec-GPC": "1",
        "Referer": "https://consolex.ai/",
        "Connection": "keep-alive"
    }
    
    proxies = {"http": args.proxy, "https": args.proxy} if args and args.proxy else None
    
    try:
        log_message(f"Attempting to get new token for {email}", "info", args)
        response = requests.post(
            login_url,
            headers=headers,
            json={"email": email, "password": password},
            proxies=proxies
        )
        response.raise_for_status()
        token = response.json().get("access_token")
        if token:
            log_message("Successfully obtained new token", "info", args)
            return token
        else:
            log_message(f"Unexpected response: {response.text}", "error", args)
            return None
    except requests.exceptions.RequestException as e:
        log_message(f"Error getting new token: {e}", "error", args)
        return None
    except json.JSONDecodeError as e:
        log_message(f"Error parsing login response: {e}", "error", args)
        return None


def verify_credentials(email, password, args=None):
    """Verify credentials with Evalsone API without saving token"""
    login_url = "https://api.evalsone.com/api/user/login"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:136.0) Gecko/20100101 Firefox/136.0",
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json;charset=utf-8",
        "Origin": "https://consolex.ai",
        "Referer": "https://consolex.ai/"
    }
    
    proxies = {"http": args.proxy, "https": args.proxy} if args and args.proxy else None
    
    try:
        response = requests.post(
            login_url,
            headers=headers,
            json={"email": email, "password": password},
            proxies=proxies
        )
        return response.status_code == 200
    except:
        return False

def send_evalsone_request(messages, token, model_id, request_params, args=None):
    """Send request to Evalsone API"""
    api_url = "https://api.evalsone.com/api/llm/chatcomplete"

    payload = {
        "messages": messages,
        "model_id": model_id,
        "max_tokens": request_params.get("max_tokens", 2048),
        "top_p": 1,
        "stream": request_params.get("stream", False),
        "toolCalls": False,
        "tool_choice": "auto",
        "auto_invoke": 0,
        "save_cost": 0,
        "artifact_mode": 0,
        "functions": [],
        "presence_penalty": request_params.get("presence_penalty"),
        "frequency_penalty": request_params.get("frequency_penalty"),
        "temperature": request_params.get("temperature", 0.5),
        "mcps": []
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:135.0) Gecko/20100101 Firefox/135.0",
        "Accept": "*/*",
        "Content-Type": "application/json",
        "Blade-auth": token
    }

    proxies = {"http": args.proxy, "https": args.proxy} if args and args.proxy else None

    try:
        model_name = next((m["model_name"] for m in models_data if m["model_id"] == model_id), None)
        response = requests.post(
            api_url,
            headers=headers,
            json=payload,
            proxies=proxies,
            stream=payload["stream"]
        )
        
        if response.status_code == 401:
            return None, "token_expired"
            
        response.raise_for_status()

        if payload["stream"]:
            def generate():
                stream_id = f"chatcmpl-{int(time.time())}"
                created_time = int(time.time())
                received_final_chunk = False

                for line in response.iter_lines():
                    if line:
                        raw_data = line.decode('utf-8').strip()
                        
                        # Handle existing data: prefix from Evalsone
                        if raw_data.startswith("data: "):
                            clean_data = raw_data[6:]  # Remove Evalsone's data: prefix
                            
                            try:
                                evalsone_chunk = json.loads(clean_data)
                                
                                # Skip empty content chunks except final one
                                content = evalsone_chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
                                finish_reason = evalsone_chunk.get("finish_reason")
                                
                                if not content and not finish_reason:
                                    continue
                                
                                # Transform to target format
                                target_chunk = {
                                    "id": stream_id,
                                    "object": "chat.completion.chunk",
                                    "created": created_time,
                                    "model": model_name,
                                    "choices": [{
                                        "index": 0,
                                        "delta": {
                                            "role": "assistant",
                                            "content": content,
                                            "tool_calls": None
                                        },
                                        "finish_reason": finish_reason,
                                        "logprobs": None
                                    }],
                                    "system_fingerprint": "fp_06737a9306",
                                    "usage": None
                                }
                                
                                # Send the transformed chunk
                                yield f"{json.dumps(target_chunk)}\n\n"
                                
                                if finish_reason == "stop":
                                    received_final_chunk = True
                                    break

                            except json.JSONDecodeError:
                                continue

                # Add mandatory stop chunk if not received
                if not received_final_chunk:
                    final_chunk = {
                        "id": stream_id,
                        "object": "chat.completion.chunk",
                        "created": created_time,
                        "model": model_name,
                        "choices": [{
                            "index": 0,
                            "delta": {
                                "role": "assistant",
                                "content": "",
                                "tool_calls": None
                            },
                            "finish_reason": "stop",
                            "logprobs": None
                        }],
                        "system_fingerprint": "fp_06737a9306",
                        "usage": {}
                    }
                    yield f"{json.dumps(final_chunk)}\n\n"

                yield "[DONE]\n\n"

            return generate(), None

        # Handle non-streaming response
        response_data = response.json()
        return {
            "content": response_data.get("choices", [{}])[0].get("message", {}).get("content", ""),
            "model": model_name,
            "object": "chat.completion",
            "created": int(time.time())
        }, None

    except requests.exceptions.RequestException as e:
        log_message(f"Request failed: {e}", "error", args)
        return None, str(e)
    except Exception as e:
        log_message(f"Unexpected error: {e}", "error", args)
        return None, str(e)

def send_deepinfra_request(messages, model_id, request_params, args=None):
    """Send request to DeepInfra API"""
    api_url = "https://api.deepinfra.com/v1/openai/chat/completions"
    
    # Ensure each message has 'role' and 'content'
    formatted_messages = []
    for msg in messages:
        if isinstance(msg, dict) and 'role' in msg and 'content' in msg:
            formatted_messages.append({
                'role': msg['role'],
                'content': msg['content']
            })
        else:
            log_message(f"Invalid message format: {msg}", "error", args)
            return None, "Invalid message format"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:135.0) Gecko/20100101 Firefox/135.0",
        "Accept": "text/event-stream" if request_params.get("stream", False) else "application/json",
        "Accept-Language": "en-US,fr;q=0.8,fr-FR;q=0.5,en;q=0.3",
        "Content-Type": "application/json",
        "Origin": "https://deepinfra.com",
        "Referer": "https://deepinfra.com/",
        "X-Deepinfra-Source": "web-page"
    }

    payload = {
        "model": model_id,
        "messages": formatted_messages,
        "stream": request_params.get("stream", False)
    }
    
    # Only add optional parameters if they're not None
    if request_params.get("max_tokens"):
        payload["max_tokens"] = request_params["max_tokens"]
    if request_params.get("temperature") is not None:
        payload["temperature"] = request_params["temperature"]
    if request_params.get("presence_penalty") is not None:
        payload["presence_penalty"] = request_params["presence_penalty"]
    if request_params.get("frequency_penalty") is not None:
        payload["frequency_penalty"] = request_params["frequency_penalty"]

    proxies = {"http": args.proxy, "https": args.proxy} if args and args.proxy else None

    try:
        response = requests.post(
            api_url,
            headers=headers,
            json=payload,
            proxies=proxies,
            stream=payload["stream"]
        )
        
        response.raise_for_status()
        
        if payload["stream"]:
            def generate():
                for line in response.iter_lines():
                    if line:
                        try:
                            # Decode using utf-8 and handle any encoding issues
                            decoded_line = line.decode('utf-8')
                            yield decoded_line
                        except UnicodeDecodeError as e:
                            log_message(f"Unicode decode error: {e}", "error", args)
                            continue
            return generate(), None
            
        return response.json(), None

    except requests.exceptions.HTTPError as e:
        log_message(f"DeepInfra HTTP error: {e.response.text}", "error", args)
        return None, f"HTTP {e.response.status_code}: {e.response.text}"
    except Exception as e:
        log_message(f"DeepInfra request failed: {e}", "error", args)
        return None, str(e)

def send_pai_request(messages, model_id, request_params, args=None):
    """Send request to Pollinations AI API"""
    api_url = "https://text.pollinations.ai/openai"
    
    headers = {
        "Content-Type": "application/json"
    }

    payload = {
        "model": model_id,
        "messages": messages,
        "stream": request_params.get("stream", False)
    }

    proxies = {"http": args.proxy, "https": args.proxy} if args and args.proxy else None

    try:
        response = requests.post(
            api_url,
            headers=headers,
            json=payload,
            proxies=proxies,
            stream=payload["stream"]
        )
        
        response.raise_for_status()
        
        if payload["stream"]:
            return response.iter_lines(), None
            
        # For non-streaming responses, clean up the response
        response_data = response.json()
        
        # Remove content filter results and usage data
        if "choices" in response_data and len(response_data["choices"]) > 0:
            for choice in response_data["choices"]:
                if "content_filter_results" in choice:
                    del choice["content_filter_results"]
        if "usage" in response_data:
            del response_data["usage"]
            
        return response_data, None

    except requests.exceptions.RequestException as e:
        log_message(f"PAI request failed: {e}", "error", args)
        return None, str(e)
    except Exception as e:
        log_message(f"Unexpected error in PAI request: {e}", "error", args)
        return None, str(e)

def get_user_id_from_token(token):
    """Extract user ID from JWT token"""
    try:
        # Get the payload part (second segment) of the JWT
        payload = token.split('.')[1]
        # Add padding if needed
        payload += '=' * (-len(payload) % 4)
        # Decode base64 and parse JSON
        decoded = json.loads(base64.b64decode(payload).decode('utf-8'))
        return decoded.get('sub')
    except Exception as e:
        log_message(f"Error decoding JWT token: {e}", "error")
        return None

def get_balance_info(token, user_id, args=None):
    """Get balance info from Evalsone API"""
    api_url = "https://api.evalsone.com/api/balance/get_info"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:135.0) Gecko/20100101 Firefox/135.0",
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json;charset=utf-8",
        "Blade-auth": token,
        "Origin": "https://evalsone.com",
        "Referer": "https://evalsone.com/"
    }

    proxies = {"http": args.proxy, "https": args.proxy} if args and args.proxy else None

    try:
        response = requests.post(
            api_url,
            headers=headers,
            json={"user_id": user_id},
            proxies=proxies
        )
        
        if response.status_code == 401:
            return None, "token_expired"
            
        response.raise_for_status()
        data = response.json()
        
        if data.get("succ") == 1 and "info" in data:
            return {
                "DI_balance": "unlimited",
                "DI_user_id": "n/a",
                "ES_balance": float(data["info"]["balance"]),
                "ES_user_id": data["info"]["user_id"]
            }, None
        else:
            return None, "Invalid response format"

    except requests.exceptions.RequestException as e:
        log_message(f"Balance request failed: {e}", "error", args)
        return None, str(e)
    except Exception as e:
        log_message(f"Unexpected error in balance request: {e}", "error", args)
        return None, str(e)

@app.route("/v1/balance", methods=["GET"])
def get_balance():
    args = parse_args()
    try:
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            log_message("Missing Authorization header for balance request", "error", args)
            return jsonify({"error": "Missing Authorization header"}), 401

        email, password = decode_auth_token(auth_header)
        if not email or not password:
            log_message("Invalid authorization token for balance request", "error", args)
            return jsonify({"error": "Invalid authorization token"}), 401

        token = tokens_data.get(email, {}).get("access_token")
        if not token:
            token = get_new_token(email, password, args)
            if token:
                tokens_data[email] = {"access_token": token}
                save_tokens(tokens_data)
            else:
                return jsonify({"error": "Failed to authenticate"}), 401

        user_id = get_user_id_from_token(token)
        if not user_id:
            return jsonify({"error": "Failed to extract user ID from token"}), 500

        result, error = get_balance_info(token, user_id, args)
        
        if error == "token_expired":
            token = get_new_token(email, password, args)
            if token:
                tokens_data[email] = {"access_token": token}
                save_tokens(tokens_data)
                user_id = get_user_id_from_token(token)
                if user_id:
                    result, error = get_balance_info(token, user_id, args)
                else:
                    return jsonify({"error": "Failed to extract user ID from new token"}), 500
            else:
                return jsonify({"error": "Failed to refresh token"}), 401
        
        if error:
            return jsonify({"error": f"Balance request failed: {error}"}), 500

        # Add PAI category to the result
        if result:
            result["PAI_balance"] = "unlimited"
            result["PAI_user_id"] = "n/a"
            
        return jsonify(result)

    except Exception as e:
        log_message(f"Unexpected error in get_balance: {e}", "error", args)
        return jsonify({"error": str(e)}), 500

@app.route("/v1/models", methods=["GET"])
def list_models():
    args = parse_args()
    try:
        model_list = []
        for model in models_data:
            model_list.append({
                "id": model["model_name"],
                "object": "model",
                "created": 1999999999,
                "owned_by": "system"
            })

        return jsonify({
            "object": "list",
            "data": model_list
        })

    except Exception as e:
        log_message(f"Unexpected error in list_models: {e}", "error", args)
        return jsonify({"error": str(e)}), 500

@app.route("/v1/chat/completions", methods=["POST"])
def chat_completions():
    args = parse_args()
    try:
        try:
            data = request.get_json()
        except json.JSONDecodeError as e:
            log_message(f"Invalid JSON in request body: {e}", "error", args)
            return jsonify({"error": "Invalid JSON in request body"}), 400

        messages = data.get("messages", [])
        if not messages:
            log_message("No messages in request", "error", args)
            return jsonify({"error": "No messages provided"}), 400

        model_name = data.get("model", "")
        if not model_name:
            log_message("No model name provided", "error", args)
            return jsonify({"error": "Model name is required"}), 400

        model_info = next((model for model in models_data if model["model_name"] == model_name), None)
        if not model_info:
            log_message(f"Invalid model name: {model_name}", "error", args)
            return jsonify({"error": "Invalid model name"}), 400

        request_params = {
            "max_tokens": data.get("max_tokens"),
            "frequency_penalty": data.get("frequency_penalty"),
            "presence_penalty": data.get("presence_penalty"),
            "temperature": data.get("temperature"),
            "stream": data.get("stream", False)
        }

        # Handle PAI models (no auth required)
        if model_info["provider"] == "PAI":
            result, error = send_pai_request(messages, model_info["model_id"], request_params, args)
            if error:
                return jsonify({"error": f"PAI request failed: {error}"}), 500
                
            if request_params["stream"]:
                def generate():
                    try:
                        for line in result:
                            line = line.decode("utf-8").strip()  # Decode bytes to string
                            if line:  
                                yield f"{line}\n\n"  # Ensure it follows SSE format
                    except Exception as e:
                        log_message(f"Stream encoding error: {e}", "error", args)
                        yield f"data: [ERROR] Failed to encode response\n\n"

                return Response(stream_with_context(generate()), mimetype='text/event-stream')
            return jsonify(result)

        # Handle DeepInfra models (no auth required)
        if model_info["provider"] == "DI":
            result, error = send_deepinfra_request(messages, model_info["model_id"], request_params, args)
            if error:
                return jsonify({"error": f"DeepInfra request failed: {error}"}), 500
                
            if request_params["stream"]:
                def generate():
                    try:
                        for line in result:
                            yield f"{line}\n\n"
                    except Exception as e:
                        log_message(f"Stream encoding error: {e}", "error", args)
                        yield f"data: [ERROR] Failed to encode response\n\n"
                return Response(stream_with_context(generate()), mimetype='text/event-stream')
            return jsonify(result)
            
        # Handle Evalsone models (auth required)
        else:  
            auth_header = request.headers.get('Authorization')
            if not auth_header:
                log_message("Missing Authorization header for Evalsone model", "error", args)
                return jsonify({"error": "Missing Authorization header"}), 401

            email, password = decode_auth_token(auth_header)
            if not email or not password:
                log_message("Invalid authorization token for Evalsone model", "error", args)
                return jsonify({"error": "Invalid authorization token"}), 401

            token = tokens_data.get(email, {}).get("access_token")
            result, error = send_evalsone_request(messages, token, model_info["model_id"], request_params, args)
            
            if error == "token_expired":
                token = get_new_token(email, password, args)
                if token:
                    tokens_data[email] = {"access_token": token}
                    save_tokens(tokens_data)
                    result, error = send_evalsone_request(messages, token, model_info["model_id"], request_params, args)
                else:
                    return jsonify({"error": "Failed to refresh token"}), 401
                
            if error:
                return jsonify({"error": f"Evalsone request failed: {error}"}), 500

            if request_params["stream"]:
                def generate():
                    for line in result:
                        yield f"data: {line.strip()}\n\n"
                return Response(stream_with_context(generate()), mimetype='text/event-stream')

            response_data = {
                "id": str(result["created"]),
                "object": result.get("object", "chat.completion"),
                "created": result.get("created", int(time.time())),
                "model": model_name,
                "choices": [{"message": {"role": "assistant", "content": result.get("content", "")}}]
            }
            
            return jsonify(response_data)

    except Exception as e:
        log_message(f"Unexpected error: {e}", "error", args)
        return jsonify({"error": str(e)}), 500

# [Previous imports and functions remain the same until main]

if __name__ == "__main__":
    args = parse_args()
    
    if not args.disable_log and not os.path.exists(LOG_FILE):
        open(LOG_FILE, 'a').close()
        log_message("Created new log file", "info", args)
    
    # Check for SSL certificates
    ssl_context = None
    default_port = 80
    
    if os.path.exists("certs/cert.pem") and os.path.exists("certs/key.pem"):
        ssl_context = ("certs/cert.pem", "certs/key.pem")
        default_port = 443
        log_message("Starting server with HTTPS...", "info", args)
    else:
        log_message("Starting server with HTTP...", "info", args)
    
    port = args.port if args.port is not None else default_port
    log_message(f"Using port {port}", "info", args)
    load_models()
    load_tokens()
    app.run(debug=False, host="0.0.0.0", port=port, ssl_context=ssl_context)
