import requests
import time
import json
import sys
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# Check if verbose or no-cfg-writing flags are provided
verbose = '--verbose' in sys.argv
no_cfg_writing = '--no-cfg-writing' in sys.argv

# Helper function for verbose output
def log_verbose(message):
    if verbose:
        print(message)

# Step 1: Create a temporary inbox
def create_temp_email():
    log_verbose("Creating temporary email...")
    url = "https://api.tempmail.lol/v2/inbox/create"
    payload = {
        "domain": "",  # Empty for random domain selection
        "prefix": ""   # Empty for random prefix
    }
    response = requests.post(url, json=payload)
    log_verbose(f"Create Temp Email Response: {response.status_code} - {response.text}")
    if response.status_code == 201:
        email_data = response.json()
        return email_data['address'], email_data['token']
    else:
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

# Step 4: Save credentials to a file
def save_credentials(temp_email, password, access_token):
    credentials = {
        "email": temp_email,
        "password": password,
        "access_token": access_token
    }
    with open("credentials.json", "a") as file:
        json.dump(credentials, file, indent=4)
    log_verbose("Credentials saved to credentials.json")

# Step 5: Set up Selenium to visit the confirmation link
def selenium_visit_link(verification_link):
    log_verbose(f"Visiting verification link: {verification_link}")
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode
    chrome_options.add_argument("--disable-gpu")
    driver = webdriver.Chrome(options=chrome_options)

    driver.get(verification_link)  # Navigate to the verification link
    log_verbose(f"Visited the verification link: {verification_link}")
    
    # Wait for a few seconds to ensure the page loads
    time.sleep(0.5)

    # Close the Selenium session after visiting the link
    driver.quit()

# Step 6: Log in and get the access token
def login_and_get_token(temp_email, password):
    if not verbose:
        print("Logging in...")
    log_verbose(f"Logging in with email: {temp_email}")
    url = "https://api.evalsone.com/api/user/login"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:136.0) Gecko/20100101 Firefox/136.0',
        'Accept': 'application/json, text/plain, */*',
        'Content-Type': 'application/json;charset=utf-8',
        'Origin': 'https://consolex.ai',
        'Referer': 'https://consolex.ai/',
    }
    payload = {
        "email": temp_email,
        "password": password
    }
    response = requests.post(url, json=payload, headers=headers)
    log_verbose(f"Login Response: {response.status_code} - {response.text}")
    if response.status_code == 200:
        log_verbose("Login successful!")
        return response.json().get('access_token')
    else:
        log_verbose("Login failed.")
        return None

# Step 7: Write access token to cfg.json
def write_auth_token_to_cfg(access_token):
    if not no_cfg_writing:
        cfg_file_path = 'cfg.json'
        try:
            with open(cfg_file_path, 'r') as file:
                cfg = json.load(file)
            cfg['auth_key'] = access_token
            with open(cfg_file_path, 'w') as file:
                json.dump(cfg, file, indent=4)
            log_verbose(f"Access token written to {cfg_file_path}")
        except Exception as e:
            log_verbose(f"Error writing to {cfg_file_path}: {e}")

# Main logic
def automate_registration(password):
    if not verbose:
        print("Starting the registration process...")

    # Create a temporary email
    temp_email, token = create_temp_email()
    if not temp_email:
        return

    # Sign up with the temporary email
    if not sign_up(temp_email, password):
        return
    
    while True:
        # Check inbox every 3 seconds
        confirmation_link = fetch_inbox(token)
        if confirmation_link:
            if not verbose:
                print("Verification email found. Visiting confirmation link...")

            # Use Selenium to visit the verification link
            selenium_visit_link(confirmation_link)

            # Log in and get the access token
            access_token = login_and_get_token(temp_email, password)
            if access_token:
                save_credentials(temp_email, password, access_token)
                write_auth_token_to_cfg(access_token)
                if not verbose:
                    print(f"Access Token: {access_token}")
            break
        else:
            if verbose:
                print("No email found, checking again in 3 seconds...")
        time.sleep(0.5)

# Run the automation with the specified password
automate_registration("xConsole2019!")
