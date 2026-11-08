# LLM experiments

Standalone scripts that exercise the OpenAI Responses API before it is wired into the
email pipeline. Run them from the repository root.

Requires `OPENAI_API_KEY` in `.env` and an account with API credits.

| File | What it shows | Command |
|---|---|---|
| `openai-quickstart.py` | A basic call, with `instructions` + `input` and with a message list | `uv run week2/openai-quickstart.py` |
| `structured_output.py` | Extraction into a JSON schema and into a Pydantic model (`responses.parse`) | `uv run week2/structured_output.py` |
| `pydantic-introduction.ipynb` | Pydantic field types, constraints, and nested models | Open in VS Code and select the `.venv` kernel |

The notebook needs the dev dependencies (`uv sync` installs them by default).
