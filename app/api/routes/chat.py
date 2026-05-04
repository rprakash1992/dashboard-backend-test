from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, List, Optional
from pydantic import BaseModel
from uuid import uuid4

from app.core.dependencies import get_current_user_id
from app.models.chat import ChatResponse, ThreadCreateResponse, TextPart, Thread_item
from app.services.openai_client import get_structured_response

router = APIRouter()
thread_store: Dict[str, List[Thread_item]] = {}


class ChatRequest(BaseModel):
    prompt: str
    thread_id: Optional[str] = None


class ThreadRequest(BaseModel):
    thread_id: Optional[str] = None


@router.post("/chat/threads", response_model=ThreadCreateResponse)
def create_thread(
    requestBody: ThreadRequest,
    loggedin_user_id: str = Depends(get_current_user_id),
):
    thread_id = requestBody.thread_id
    thread_data = None

    if not thread_id:
        thread_id = str(loggedin_user_id)

    thread_store.setdefault(thread_id, [])
    thread_data = thread_store[thread_id]
    return ThreadCreateResponse(thread_id=thread_id, thread_data=thread_data)


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest,
    loggedin_user_id: str = Depends(get_current_user_id),
):
    """
    Receives a chat prompt in the request body and returns a structured response.
    """
    prompt = request.prompt
    thread_id = request.thread_id
    
    if not request.thread_id:
        thread_id = str(loggedin_user_id)
        
    if thread_id not in thread_store:
        raise HTTPException(status_code=404, detail="Unknown thread_id")

    new_part = TextPart(type="text", data=prompt)
    new_thread_content = ChatResponse(parts=[new_part], suggestions=[])
    new_thread_item = Thread_item(
        id=str(uuid4()), role="user", relevant=None, content=new_thread_content)
    thread_store[thread_id].append(new_thread_item)

    response = await get_structured_response(prompt)
    new_thread_item = Thread_item(
        id=str(uuid4()),
        role="assistant",
        relevant=None,
        content=response,
    )
    thread_store[thread_id].append(new_thread_item)

    return response
