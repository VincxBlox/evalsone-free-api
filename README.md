# AIDOC-free-api
 Provides AIDOC unlimited API to all.


# !!!! VERY MUCH EXPERIMENTAL!
# DO NOT USE THIS IN A PRODUCTION ENVIRONMENT.
# and its currently complete shit but it works

I am not responsible for the usage of this script. If any of the owners of these services wants me to tkae it down off of this, simply contact me.


## Runtime Arguments
- --proxy # to set a proxy
- --verbose # to get all output
- --disable-logs # to disable logging to file
- --port # to set a port for the serv to run on



## Features

- ITS FREE AND UNLIMITED!
- OpenAI request and response structure!!!
- Includes detailed logging and verbosity options.
- Integrated proxy support.


## Getting Started

### Prerequisites

- Python 3.8+
- Flask
- Flask-cors
- aiohttp

### Installation

1. Clone this repository

2. Install required Python libraries:
   ```bash
   pip3 install flask flask-cors aiohttp
   ```
3: pray that it works:
   ```bash
   echo *praying*
   ```


4. Run the application:
   ```bash
   python3 api.py
   ```

## Usage

- **Starting the Server**: The Flask server will run on the configured port (default is `80`). Access it at `http://127.0.0.1`.
- **Logs**: If logging is enabled, logs will be saved to `logs.txt`.
- **Proxy**: If a proxy server is required, specify it at runtime (--proxy).
- Now, you can use the openai module to send and receive requests with the following models:

## Models

gemini-2.0-flash  
o4-mini  
o4-mini-high  
gpt-4o-mini  
gpt-4o  
claude-3-opus  
claude-3.7-sonnet  (sometimes just doesnt work it depends)
claude-3.5-sonnet  
gemini-2.5-flash  
deepseek-r1  
qwen-qwq  
llama-4-maverick  
llama-4  
llama-4-scout  
llama-3.3  
gemini-2.5-pro  
o3-mini  
gpt-4.1  
gpt-4.1-mini

(read the models.json AIDOC part only to know the exact model. DI is in progress.)

## FAQ


500 http error, what does this mean?
that means an error occured on their end or something is fucked in the request. it may do that if you send a very large text for example too...

the ai says nothing???
yea claude 3.7 usually does that, even when it reports http 200, and some others models sometimes

conversation history issues?
read the 3rd known issue.
## Contributing

contributions are welcome! submit a pull request for review.


## KNOWN ISSUES PLEASE READ
It is not rare for it to simply not work, that happens

The script does support sending streaming chunks, but the internal API DOES NOT, so there will be NO actual stream, but apps that depends on streaming will still work.

There might be some issues with the CONVERSATION history. The endpoint works in a progressive messages system, so you can't pass existing messages throught the request, so the only solution i had was to tell it the past messages, and that usually works, but not always. It might start saying some shit like 
   ```text
   I understand you've provided conversation history and a new message, but I should respond as myself based on my actual capabilities and instructions. 
   ```



## Contact

For any questions or issues, feel free to open an issue on GitHub or contact me at:
vincemartineau@outlook.com
or Discord:
~~vince.hd~~ ban atm.