import json
import multiprocessing
import os

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, UploadFile
from openai import OpenAI
from typing import Any, Dict
from uvicorn import run

load_dotenv()

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', None)
OPENAI_MODEL = os.getenv("OPENAI_MODEL", None)
PORT = int(os.getenv("PORT", 8081))

app = FastAPI()


def parse_json_from_response(response) -> Dict[str, Any]:
    # Chat Completions JSON-schema responses are normally valid JSON in message.content.
    content = response.choices[0].message.content
    return json.loads(content)

def parse_history(messages: str | None) -> list[Dict[str, str]]:
    """Parse the chat history sent by Tilbot: a JSON list of {"role", "content"}."""
    if not messages:
        return []
    try:
        parsed = json.loads(messages)
    except json.JSONDecodeError:
        return []
    if not isinstance(parsed, list):
        return []
    return [
        {"role": m["role"], "content": m["content"]}
        for m in parsed
        if isinstance(m, dict)
        and m.get("role") in ("user", "assistant")
        and isinstance(m.get("content"), str)
    ]

@app.get("/healthcheck")
async def healthcheck():
    return {"status": "ok"}

@app.post("/")
async def get_chatgpt_response(image: UploadFile = File(None),
    user_input: str = Form(""),
    prompt: str | None = Form(None),
    intent_options: str | None = Form(None),
    key_user_account: str | None = Form(None),
    messages: str | None = Form(None),
):

    intent_options_parsed = json.loads(intent_options) if intent_options else []
    history = parse_history(messages)

    api_key = OPENAI_API_KEY
    if key_user_account is not None and api_key is not None:
        api_key += "_" + key_user_account

    client = OpenAI(api_key=api_key)

    input_text = user_input or prompt or ""
    model_input = history + [{"role": "user", "content": input_text}] if history else input_text

    print(model_input)

    if len(intent_options_parsed) > 0:
        description = "Find the best matching intent from the provided options. If none match, return 'unknown'."
        if prompt is not None:
            description = prompt
            
        response_format = {
            "format": {
                "type": "json_schema",
                "name": "intent_result",
                "strict": True,
                "schema": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "intent": {
                            "type": "string",
                            "enum": intent_options_parsed,
                            "description": description
                        }
                    },
                    "required": ["intent"]
                }
            }
        }

        message = client.responses.parse(
            model=OPENAI_MODEL,
            instructions=prompt,
            input=model_input,
            text=response_format
        )

        results = json.loads(message.output_text)
        if results["intent"] not in intent_options_parsed or results["intent"] == "unknown":
            return None
        else:
            return {"intent": results["intent"], "connector_label": results["intent"]}
    else:
        message = client.responses.parse(
            model=OPENAI_MODEL,
            instructions=prompt,
            input=model_input
        )

        return {"intent": message.output_text, "connector_label": message.output_text}

if __name__ == "__main__":
    multiprocessing.freeze_support()  # For Windows support
    run(app, host="0.0.0.0", port=PORT, reload=False, workers=1)
