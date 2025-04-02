# AI Shell

AI Shell is a powerful command-line tool that converts natural language into CLI commands. It uses a hybrid approach with both local LLM (TinyLlama) and cloud-based AI services to generate accurate commands for your operating system.

## Features

- Convert natural language to CLI commands
- Support for Windows, Linux, and macOS
- Local LLM for offline operation
- Cloud API integration (Claude, OpenAI, DeepSeek)
- Command caching for faster responses
- SSH remote execution support
- Auto-correction for typos


## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python ai_shell.py
```

## Usage

1. Type your request in natural language:
   ```
   AI-Shell> show all docker containers
   ```

2. AI Shell will generate the appropriate command:
   ```
   Command: docker ps -a
   ```

3. Choose an option:
   - `y` to execute the command
   - `n` to skip execution
   - `r` to regenerate with a different AI model

## Special Commands

- `\help` - Show help guide
- `\config` - Configure API keys and model settings
- `exit shell` - Exit the application

## Configuration

Use the `\config` command to:
- Set API provider (Claude, OpenAI, DeepSeek, or offline mode)
- Configure API keys
- Download or update the local LLM model


## License

This project is licensed under the MIT License - see the LICENSE file for details.
