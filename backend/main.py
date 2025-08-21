import asyncio
import json

import boto3
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

app = FastAPI()
load_dotenv()

knowledge_base_id = "JGMPKF6VEI"


class Message(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    messages: list[Message]


def get_bedrock_client():
    return boto3.client("bedrock-runtime", region_name="us-east-1")


def invoke_llm(messages: list[dict]):
    client = get_bedrock_client()

    payload = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 1000,
        "temperature": 0.7,
        "system": "You are a helpful assistant.",
        "messages": messages,
    }

    model = "us.anthropic.claude-3-7-sonnet-20250219-v1:0"
    response = client.invoke_model(
        modelId=model,
        body=json.dumps(payload),
        contentType="application/json",
        accept="application/json",
    )

    result_bytes = response["body"].read()
    result_json = json.loads(result_bytes.decode("utf-8"))

    content = result_json.get("content", [])
    if content and len(content) > 0:
        return content[0].get("text", "")
    return ""


async def stream_generator(messages: list[dict]):
    response = invoke_llm(messages)
    for word in response.split():
        yield word + " "
        await asyncio.sleep(0.05)


def query_kb(messages: list[dict]) -> str:
    client = get_bedrock_client()

    payload = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 500,
        "temperature": 0.7,
        "system": f"You are a helpful assistant. Use the knowledge base {knowledge_base_id} when relevant.",
        "messages": messages,
    }

    model_id = "us.anthropic.claude-3-7-sonnet-20250219-v1:0"
    response = client.invoke_model(
        modelId=model_id,
        body=json.dumps(payload),
        contentType="application/json",
        accept="application/json",
    )

    result_bytes = response["body"].read()
    result_json = json.loads(result_bytes.decode("utf-8"))
    content = result_json.get("content", [])

    if content and len(content) > 0:
        return content[0].get("text", "")
    return "No response generated"


async def stream_kb(messages: list[dict]):
    answer = query_kb(messages)
    for word in answer.split():
        yield word + " "
        await asyncio.sleep(0.05)


# LLM endpoints
@app.post("/llm/query")
def query_llm_endpoint(request: ChatRequest):
    try:
        messages = [m.dict() for m in request.messages]
        response = invoke_llm(messages)
        return {"response": response}
    except Exception as e:
        return {"error": str(e)}


@app.post("/llm/stream")
async def stream_llm_endpoint(request: ChatRequest):
    messages = [m.dict() for m in request.messages]
    return StreamingResponse(stream_generator(messages), media_type="text/plain")


# KB endpoints
@app.post("/kb/query")
def kb_query_endpoint(request: ChatRequest):
    try:
        messages = [m.dict() for m in request.messages]
        answer = query_kb(messages)
        return {"answer": answer}
    except Exception as e:
        return {"error": str(e)}


@app.post("/kb/stream")
async def kb_stream_endpoint(request: ChatRequest):
    messages = [m.dict() for m in request.messages]
    return StreamingResponse(stream_kb(messages), media_type="text/plain")
