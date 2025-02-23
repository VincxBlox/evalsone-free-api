import requests
import time
import json
import sys
import base64
import random
import string

# Check if verbose or no-cfg-writing flags are provided
verbose = '--verbose' in sys.argv
no_cfg_writing = '--no-cfg-writing' in sys.argv

# Helper function for verbose output
def log_verbose(message):
    if verbose:
        print(message)

def create_temp_email():
    log_verbose("Creating temporary email...")
    while True:
        url = "https://api.tempmail.lol/v2/inbox/create"
        payload = {
            "domain": "",  # Empty for random domain selection
            "prefix": ""   # Empty for random prefix
        }
        response = requests.post(url, json=payload)
        log_verbose(f"Create Temp Email Response: {response.status_code} - {response.text}")
        if response.status_code == 201:
            email_data = response.json()
            # Check if domain is .com
            if email_data['address'].endswith('undeadbank.com'):
                return email_data['address'], email_data['token']
            else:
                log_verbose("Non undeadbank.com domain received, trying again in a second...")
                time.sleep(1.5)
                continue
        else:
            if response.status_code == 429:
                print("got rate limit by tempmail.lol. waiting 5min as the tempmail.lol docs say.")
                time.sleep(300)
                continue
            log_verbose("Failed to create inbox.")
            return None, None

# Step 2: Sign up using the temporary email
def sign_up(temp_email, password):
    if not verbose:
        print("Signing up...")
    log_verbose(f"Signing up with email: {temp_email}")
    url = "https://api.evalsone.com/api/user/register"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:136.0) Gecko/20100101 Firefox/136.0',
        'Accept': 'application/json, text/plain, */*',
        'Content-Type': 'application/json;charset=utf-8',
        'Origin': 'https://consolex.ai',
        'Referer': 'https://consolex.ai/',
    }
    payload = {
        "email": temp_email,
        "password": password,
        "lang": "en",
        "source": "consolex"
    }
    response = requests.post(url, json=payload, headers=headers)
    log_verbose(f"Sign Up Response: {response.status_code} - {response.text}")
    if response.status_code == 200:
        log_verbose("Sign up successful!")
        return True
    else:
        log_verbose("Sign up failed.")
        return False

# Step 3: Fetch the email to find the confirmation link
def fetch_inbox(token):
    log_verbose("Checking inbox for confirmation link...")
    url = f"https://api.tempmail.lol/v2/inbox?token={token}"
    response = requests.get(url)
    log_verbose(f"Fetch Inbox Response: {response.status_code} - {response.text}")
    if response.status_code == 200:
        emails = response.json().get('emails', [])
        if emails:
            for email in emails:
                # Find the verification link in the email body
                if 'href' in email.get('html', ''):
                    href_start = email['html'].find('href="') + len('href="')
                    href_end = email['html'].find('"', href_start)
                    return email['html'][href_start:href_end]
    return None

# Step 4: Fetch registration code from email
def fetch_reg_code(token):
    log_verbose("Checking inbox for registration code but wait 2 secs before...")
    url = f"https://api.tempmail.lol/v2/inbox?token={token}"
    time.sleep(2)
    response = requests.get(url)
    log_verbose(f"Fetch Inbox Response: {response.status_code} - {response.text}")
    if response.status_code == 200:
        emails = response.json().get('emails', [])
        if emails:
            for email in emails:
                # Extract the verification link from the email
                if 'href' in email.get('html', ''):
                    href_start = email['html'].find('href="') + len('href="')
                    href_end = email['html'].find('"', href_start)
                    verification_link = email['html'][href_start:href_end]
                    # Extract the registration code from the verification link
                    regcode_start = verification_link.find('regcode=') + len('regcode=')
                    regcode = verification_link[regcode_start:]
                    return regcode
    return None

# Step 5: Send registration code to the API
def send_reg_code(temp_email, password, regcode):
    log_verbose(f"Sending registration code: {regcode}")
    url = "https://api.evalsone.com/api/user/auth_regcode"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:136.0) Gecko/20100101 Firefox/136.0',
        'Accept': 'application/json, text/plain, */*',
        'Content-Type': 'application/json;charset=utf-8',
        'Origin': 'https://consolex.ai',
        'Referer': 'https://consolex.ai/',
        'Blade-auth': regcode
    }
    payload = {
        "regcode": regcode
    }
    response = requests.post(url, json=payload, headers=headers)
    log_verbose(f"Registration Code Response: {response.status_code} - {response.text}")
    if response.status_code == 200:
        # Save email and password in base64 encoded format
        api_key = base64.b64encode(json.dumps({"email": temp_email, "password": password}).encode()).decode()
        save_api_key(api_key)
        return api_key
    else:
        log_verbose("Failed to verify registration code.")
        return None

# Step 6: Save API key to a file
def save_api_key(api_key):
    with open("api_key.json", "w") as file:
        json.dump({"api_key": api_key}, file, indent=4)
    log_verbose("API key saved to api_key.json")

def generate_random_password(length=12):
    """Generates a random password with letters, digits, and one special character."""

    # Generate a random string of letters and digits
    password = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length - 1))

    # Choose a random special character
    special_chars = ['!', '?', '$']
    special_char = random.choice(special_chars)

    # Insert the special character at a random position
    password = password[:random.randint(0, length - 1)] + special_char + password[random.randint(0, length - 1):]

    return password

def login_to_get_token(email, password):
    log_verbose("Logging in to get token...")
    url = "https://api.evalsone.com/api/user/login"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:136.0) Gecko/20100101 Firefox/136.0',
        'Accept': 'application/json, text/plain, */*',
        'Content-Type': 'application/json;charset=utf-8',
        'Origin': 'https://consolex.ai',
        'Referer': 'https://consolex.ai/'
    }
    payload = {
        "email": email,
        "password": password
    }
    response = requests.post(url, json=payload, headers=headers)
    log_verbose(f"Login Response: {response.status_code} - {response.text}")
    if response.status_code == 200:
        return response.json().get('access_token')
    return None

# Main logic
def automate_registration():
    if not verbose:
        print("Starting the registration process...")

    # Create a temporary email
    temp_email, token = create_temp_email()
    if not temp_email:
        return

    # Generate a random password
    password = generate_random_password()
    log_verbose(f"Generated Password: {password}")

    # Sign up with the temporary email
    if not sign_up(temp_email, password):
        return

    while True:
        # Check inbox every 3 seconds for registration code
        regcode = fetch_reg_code(token)
        if regcode:
            api_key = send_reg_code(temp_email, password, regcode)
            evalsone_key = login_to_get_token(temp_email, password)
            if api_key:
                print(f"API Key for script: {api_key}")
                print(f"API Key for Evalsone: {evalsone_key}")
            break
        else:
            if verbose:
                print("No registration code found, checking again in 3 seconds...")
        time.sleep(3)
    input("\nPress Enter to exit...")

# Run the automation
automate_registration()