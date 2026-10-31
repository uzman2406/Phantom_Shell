# 👻 PhantomShell — The Terminal Has a Ghost

A spooky, local-first AI command companion with a polished web interface. Type a shell command and PHANTOM explains what it appears to do, highlights meaningful risks, and replies in a mysterious ghostly voice.

**Important:** PhantomShell inspects command text only. It never executes shell commands.

## Preview

Run it locally and open `http://127.0.0.1:8000`.

## Stack

- Python standard-library HTTP server
- HTML, CSS and vanilla JavaScript
- Ollama local inference
- Default model: `qwen2.5:3b` (open-weight)

## Requirements

- Python 3.9+
- [Ollama](https://ollama.com/)
- Enough RAM for the model you choose

## Run locally

1. Install Ollama: https://ollama.com/
2. Download the model:

   ```bash
   ollama pull qwen2.5:3b
   ```

3. Make sure Ollama is running. On most installations, the Ollama app starts its local service automatically.
4. Download/clone this repository and open a terminal in the project directory.
5. Start PhantomShell:

   ```bash
   python server.py
   ```

   On Windows:

   ```powershell
   py server.py
   ```

6. Visit `http://127.0.0.1:8000` in your browser.

No `pip install` step is required.

## Configuration

Set environment variables before starting the server:

| Variable | Default | Purpose |
|---|---|---|
| `PHANTOM_HOST` | `127.0.0.1` | Web server bind address |
| `PHANTOM_PORT` | `8000` | Web server port |
| `PHANTOM_MODEL` | `qwen2.5:3b` | Ollama model tag |
| `OLLAMA_HOST` | `http://localhost:11434` | Local Ollama endpoint |

PowerShell example:

```powershell
$env:PHANTOM_MODEL="llama3.2:3b"
py server.py
```

## Architecture

```text
Browser (HTML/CSS/JavaScript)
            |
            | POST /api/chat
            v
Local Python HTTP server
            |
            | POST http://localhost:11434/api/chat
            v
Ollama running on this machine
            |
            v
Open-weight model (Qwen 2.5 3B)
            |
            v
Ghostly response in browser
```

## Why open innovation?

A hosted closed API would put command text on a third-party service and could introduce usage fees, network dependency, and provider lock-in.

PhantomShell uses Ollama and an open-weight model locally:

- Command text stays on the machine when using the default localhost setup.
- After the model is downloaded, inference works without an internet connection.
- No per-request hosted inference charge or API key.
- You can swap compatible local models using an environment variable.
- The prompt and application code can be inspected and modified.

The first install and model download require internet. Local inference does not. If you expose the web server or Ollama beyond localhost, the privacy and security assumptions change; keep the default local-only binding unless you know how to secure it.

## Safety notes

- The app never passes user input to a shell.
- It only sends text to the local Ollama chat endpoint.
- It binds to `127.0.0.1` by default, so it is intended for local use.
- AI explanations can be wrong; verify important commands before running them.
- Do not paste passwords, access tokens, private keys, or other secrets into the chat.

## Project layout

```text
phantomshell-web/
├── server.py
├── static/
│   ├── index.html
│   ├── style.css
│   └── app.js
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## License

MIT
