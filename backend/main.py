import boto3
import json
import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
from datetime import datetime
from botocore.exceptions import NoCredentialsError, ClientError
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uvicorn

# Load environment variables
load_dotenv()

# AWS Configuration
AWS_CONFIG = {
    'region': os.getenv('AWS_DEFAULT_REGION', 'us-east-1'),
    'access_key': os.getenv('AWS_ACCESS_KEY_ID'),
    'secret_key': os.getenv('AWS_SECRET_ACCESS_KEY')
}

# Model configuration
model = 'us.anthropic.claude-3-7-sonnet-20250219-v1:0'

# Initialize AWS clients
client = boto3.client(
    "bedrock-runtime",
    region_name=AWS_CONFIG['region'],
    aws_access_key_id=AWS_CONFIG['access_key'],
    aws_secret_access_key=AWS_CONFIG['secret_key'],
)

bedrock_knowledge_base = boto3.client(
    "bedrock-agent-runtime",
    region_name=AWS_CONFIG['region'],
    aws_access_key_id=AWS_CONFIG['access_key'],
    aws_secret_access_key=AWS_CONFIG['secret_key'],
)

knowledge_base_id = "JGMPKF6VEI"

# Initialize FastAPI app
app = FastAPI(
    title="Knowledge Base RAG API",
    description="API for querying knowledge base using RAG and Claude",
    version="1.0.0"
)

# Pydantic models
class QueryRequest(BaseModel):
    query: str

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    system: Optional[str] = None
    temperature: Optional[float] = 0.5
    max_tokens: Optional[int] = 1024

class WeatherRequest(BaseModel):
    location: str

class KBRetrievalResponse(BaseModel):
    results: List[Dict[str, Any]]
    query: str

class RAGResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]]
    query: str

# Utility functions
def add_user_message(messages, prompt):
    user_message = {'role': 'user', 'content': prompt}
    messages.append(user_message)
    
def add_assistant_message(messages, prompt):
    assistant_message = {'role': 'assistant', 'content': prompt}
    messages.append(assistant_message)

def create_body_json(messages, max_tokens=1024, system=None, temperature=0.5, thinking=False):
    body_dict = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": max_tokens,
        "temperature": temperature,
        "messages": messages,
    }
    if system:
        body_dict['system'] = system
    
    if thinking:
        body_dict['thinking'] = {
            "type": "enabled",
            "budget_tokens": 1024,
        }
    body_json = json.dumps(body_dict)
    return body_json

def chat(messages, model_id=model, system=None, temperature=0.5, max_tokens=1024):
    params = {
        "max_tokens": max_tokens,
        "system": system,
        "temperature": temperature,
        "messages": messages
    }
    body_json = create_body_json(**params)
    try:
        response = client.invoke_model(
            modelId=model_id,
            body=body_json
        )
        message = json.loads(response['body'].read().decode('utf-8'))
        return message['content'][0]['text']
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error invoking model: {str(e)}")

def get_current_weather(location: str) -> str:
    """Get the current weather for a location.
    
    Args:
        location: The name of the city or location

    Returns:
        A string describing the current weather conditions
    """
    url = f"https://wttr.in/{location}?format=j1"  # JSON format
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        current = data['current_condition'][0]

        weather = {
            "temperature": current['temp_C'],
            "description": current['weatherDesc'][0]['value'],
            "humidity": current['humidity'],
            "wind_speed": current['windspeedKmph']
        }

        return weather

    except requests.exceptions.RequestException as err:
        return f"Request failed: {err}"
    except KeyError:
        return "Could not parse weather data."

def create_kb_request(kb_id, query, num_results=3):
    req = {
        "knowledgeBaseId": kb_id,
        "retrievalQuery": {"text": query},
        "retrievalConfiguration": {
            "vectorSearchConfiguration": {
                "numberOfResults": num_results
            }
        }
    }
    return req

# API Endpoints

@app.get("/")
async def root():
    return {"message": "Knowledge Base RAG API is running"}

@app.post("/kb-rag-query", response_model=RAGResponse)
async def kb_rag_query(request: QueryRequest):
    """
    Query the knowledge base using RAG (Retrieval Augmented Generation).
    This endpoint retrieves relevant documents and generates an answer using Claude.
    """
    try:
        # Step 1: Retrieve relevant documents from knowledge base
        kb_request = create_kb_request(knowledge_base_id, request.query)
        
        kb_response = bedrock_knowledge_base.retrieve(**kb_request)
        
        # Extract retrieved documents
        retrieved_docs = []
        context_text = ""
        
        for result in kb_response.get('retrievalResults', []):
            content = result.get('content', {}).get('text', '')
            score = result.get('score', 0)
            metadata = result.get('metadata', {})
            
            retrieved_docs.append({
                "content": content,
                "score": score,
                "metadata": metadata
            })
            
            context_text += f"Document: {content}\n\n"
        
        # Step 2: Generate answer using Claude with retrieved context
        system_prompt = """You are a helpful assistant that answers questions based on the provided context. 
        Use the retrieved documents to provide accurate and informative answers. 
        If the information is not available in the context, say so clearly."""
        
        user_prompt = f"""Context from knowledge base:
{context_text}

Question: {request.query}

Please provide a comprehensive answer based on the context provided."""

        messages = [{"role": "user", "content": user_prompt}]
        
        answer = chat(
            messages=messages,
            system=system_prompt,
            temperature=0.3,
            max_tokens=1024
        )
        
        return RAGResponse(
            answer=answer,
            sources=retrieved_docs,
            query=request.query
        )
        
    except ClientError as e:
        raise HTTPException(status_code=500, detail=f"AWS Bedrock error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing RAG query: {str(e)}")

@app.post("/kb-retrieve", response_model=KBRetrievalResponse)
async def kb_retrieve(request: QueryRequest, num_results: int = 3):
    """
    Retrieve relevant documents from the knowledge base without generating an answer.
    """
    try:
        kb_request = create_kb_request(knowledge_base_id, request.query, num_results)
        
        kb_response = bedrock_knowledge_base.retrieve(**kb_request)
        
        results = []
        for result in kb_response.get('retrievalResults', []):
            results.append({
                "content": result.get('content', {}).get('text', ''),
                "score": result.get('score', 0),
                "metadata": result.get('metadata', {})
            })
        
        return KBRetrievalResponse(
            results=results,
            query=request.query
        )
        
    except ClientError as e:
        raise HTTPException(status_code=500, detail=f"AWS Bedrock error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving from knowledge base: {str(e)}")

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """
    Chat with Claude directly without knowledge base retrieval.
    """
    try:
        messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]
        
        response = chat(
            messages=messages,
            system=request.system,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        
        return {"response": response}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in chat: {str(e)}")

@app.post("/weather")
async def weather_endpoint(request: WeatherRequest):
    """
    Get current weather for a location.
    """
    try:
        weather_data = get_current_weather(request.location)
        return {"weather": weather_data, "location": request.location}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting weather: {str(e)}")

@app.get("/health")
async def health_check():
    """
    Health check endpoint to verify API and AWS connections.
    """
    try:
        # Test AWS connection by listing available models (if permissions allow)
        # This is a simple connection test
        return {
            "status": "healthy",
            "aws_region": AWS_CONFIG['region'],
            "model": model,
            "knowledge_base_id": knowledge_base_id
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")
