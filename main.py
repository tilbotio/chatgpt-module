import json
import multiprocessing
import os

from dotenv import load_dotenv
from fastapi import FastAPI
from openai import OpenAI
from pydantic import BaseModel
from typing import Any, Dict
from uvicorn import run

load_dotenv()

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', None)
OPENAI_MODEL = os.getenv("OPENAI_MODEL", None)
PORT = os.getenv("PORT", 8081)

app = FastAPI()


class ChatRequest(BaseModel):
    user_input: str = ""
    prompt: str | None = None
    intent_options: list[str] | None = None
    key_user_account: str | None = None


def parse_json_from_response(response) -> Dict[str, Any]:
    # Chat Completions JSON-schema responses are normally valid JSON in message.content.
    content = response.choices[0].message.content
    return json.loads(content)

@app.get("/healthcheck")
async def healthcheck():
    return {"status": "ok"}

@app.post("/")
async def get_chatgpt_response(request: ChatRequest):
    user_input = request.user_input
    prompt = request.prompt
    intent_options = request.intent_options
    key_user_account = request.key_user_account

    print(intent_options)

    api_key = OPENAI_API_KEY
    if key_user_account is not None:
        api_key += "_" + key_user_account

    client = OpenAI(api_key=api_key)

    input_text = user_input or prompt or ""

    if len(intent_options) > 0:
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
                            "enum": intent_options,
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
            input=input_text,
            text=response_format
        )

        results = json.loads(message.output_text)
        if results["intent"] not in intent_options or results["intent"] == "unknown":
            return None
        else:
            return {"intent": results["intent"], "connector_label": results["intent"]}
    else:
        message = client.responses.parse(
            model=OPENAI_MODEL,
            instructions=prompt,
            input=input_text
        )

        return {"intent": "", "connector_label": message.output_text}

if __name__ == "__main__":
    multiprocessing.freeze_support()  # For Windows support
    run(app, host="0.0.0.0", port=PORT, reload=False, workers=1)
