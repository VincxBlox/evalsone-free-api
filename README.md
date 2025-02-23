# evalsone-free-api
 Provides Evalsone/DeepInfra/PollinationAI unlimited API to all.


# !!!! VERY MUCH EXPERIMENTAL!
# DO NOT USE THIS IN A PRODUCTION ENVIRONMENT.

I am not responsible for the usage of this script. If any of the owners of these services wants me to tkae it down off of this, simply contact me.


## Runtime Arguments
- --proxy # to set a proxy
- --verbose # to get all output
- --disable-logs # to disable logging to file
- --port # to set a port for the serv to run on

make_es_acc script Arguments:
- --no-cfg-writing # does not write to cfg.json, only makes an account
- --verbose # outputs everything to console



## Features

- ITS FREE AND UNLIMITED!
- OpenAI request and response structure!!!
- Includes detailed logging and verbosity options.
- Integrated proxy support.


## Getting Started

### Prerequisites

- Python 3.8+
- Flask library

### Installation

1. Clone this repository

2. Install required Python libraries:
   ```bash
   pip3 install -r requirements.txt
   ```
3: Make an Evalsone account:
   ```bash
   python3 make_es_acc.py
   ```
This will return a key for Evalsone (you dont need this typically) and key for script which is your api key for using the script with

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

The only important missing one is Claude 3.5 Sonnet.

### Evalsone models
claude-instant
claude-2
claude-2-1
claude-3-haiku
gpt-4o-mini
gemini-1-5-flash
claude-3-5-haiku
gemini-2-flash

### PollinationAI models

gpt-4o
mistral-nemo-evil
o1-mini

### DeepInfra models

llama-3-8b
lamma-3-70b
deepseek-v3
deepseek-r1
deepseek-r1-llama
deepseek-r1-qwen
phi-4
wizardlm-2-8x22b
qwen-2-5-72b
dolphin-2-6
dolphin-2-9
dbrx
airoboros-70b
lzlv-70b
wizardlm-2-70b
mixtral-8x22b

## FAQ

make_acc script just hangs at signing up! what do i do!??
~~that means you have sent too many requests to make an account.~~ PATCHED, it nows tell you when that happens.
this means that evalsone doesnt like the chosen email. i havent figured out what causes this, if it hangs for like more than 30 seconds just restart the script.
theoritally alot more could be causing this but usually its just hanging at waiting for the email (some emails just dont receive it.)

500 http error from deepinfra/evalsone/pai, what does this mean?
that means an error occured on their end or something is fucked in the request. it may do that if you send a very large text for example.

server overloaded from deepinfra
this usually happens with deepseek-r1, its very popular and it should be self explanatory. alot of people is using it at the same time.

## Contributing

contributions are welcome! submit a pull request for review.

## Contact

For any questions or issues, feel free to open an issue on GitHub or contact me at:
vincemartineau@outlook.com
or Discord:
~~vince.hd~~ ban atm.
darwiny7859