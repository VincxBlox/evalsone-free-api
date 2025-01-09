# evalsone-free-api
 Provides Evalsone unlimited API to all.


# !!!! VERY MUCH EXPERIMENTAL!

This project provides a Flask-based API server.



## Runtime Arguments
- --proxy # to set a proxy
- --verbose # to get all output
- --no-logs # to disable logging to file

make_acc script Arguments:
- --no-cfg-writing # does not write to cfg.json, only makes an account
- --verbose # outputs everything to console



## Features

- ITS FREE AND UNLIMITED!
- OpenAI request and response structure!!!
- Automatically creates a default `cfg.json` if not found.
- Loads system configuration dynamically from `cfg.json`.
- Fallback to default settings for missing configuration values.
- Supports system messages (`sys_msg`) and port customization.
- Includes detailed logging and verbosity options.
- Integrated proxy support.


## Configuration Defaults

The default configuration is as follows:

```json
{
    "auth_key": null,
    "log_file": "logs.txt",
    "verbose": false,
    "proxy": null,
    "logging_enabled": true,
    "port": 80,
    "sys_msg": "your an ai bru just work holy shit"
}
```

### Explanation of Fields

- **auth_key**: The authentication key for API access (required).
- **log_file**: The file path where logs will be stored.
- **verbose**: Boolean flag to enable or disable verbose output.
- **proxy**: Proxy server to use for API requests (if any).
- **logging_enabled**: Boolean flag to enable or disable logging.
- **port**: The port on which the Flask server will run.
- **sys_msg**: A default system message to use in the application.

## Getting Started

### Prerequisites

- Python 3.8+
- Flask library

### Installation

1. Clone this repository

2. Install required Python libraries:
   ```bash
   pip install flask asyncio selenium
   ```
Note: Selenium is not needed if not using the make_acc script.

3. Run the application:
   ```bash
   python api.py
   ```

### Initial Configuration

When you first run the application, it will check for the presence of `cfg.json` in the current working directory. If the file is missing, a default `cfg.json` will be created. You will need to:

1. Open `cfg.json` and set the `auth_key` to your API key, or run make_acc script.
2. Optionally update other configuration values as needed.

## Usage

- **Starting the Server**: The Flask server will run on the configured port (default is `80`). Access it at `http://localhost`.
- **Logs**: If logging is enabled, logs will be saved to the file specified in the `log_file` field (default is `logs.txt`).
- **System Message**: The system message (`sys_msg`) can be customized in the `cfg.json` file.
- **Proxy**: If a proxy server is required, specify it in the `proxy` field, or at runtime (--proxy).

## Error Handling

- If the `auth_key` is missing or invalid, the application will terminate with an error message.
- Missing configuration fields in `cfg.json` will be automatically replaced with default values.


## FAQ

make_acc script just hangs at signing up! what do i do!??
that means you have sent too many requests to make an account. u should wait 10-15 mins until trying again.



## Contributing

Contributions are welcome! Please fork the repository and submit a pull request for review.

## Contact

For any questions or issues, feel free to open an issue on GitHub or contact me at:
vincemartineau@outlook.com
or Discord:
vince.hd