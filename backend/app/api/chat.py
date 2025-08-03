from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc
from pydantic import BaseModel
from typing import List, Optional
import uuid
import json
import os
from datetime import datetime

from ..database.connection import get_db
from ..database.models import ChatConversation, ChatMessage
from ..services.claude_chat import ClaudeChatService

router = APIRouter()

class ChatMessageRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None

class ChatMessageResponse(BaseModel):
    id: str
    role: str
    content: str
    timestamp: datetime

class ChatHistoryResponse(BaseModel):
    conversation_id: str
    messages: List[ChatMessageResponse]

class ChatResponse(BaseModel):
    response: str
    conversation_id: str

@router.post("/message", response_model=ChatResponse)
async def send_chat_message(
    request: ChatMessageRequest,
    db: Session = Depends(get_db)
):
    """Send a message to the chat assistant and get a response."""
    try:
        # Get or create conversation
        if request.conversation_id:
            conversation = db.query(ChatConversation).filter(
                ChatConversation.conversation_id == request.conversation_id
            ).first()
            if not conversation:
                raise HTTPException(status_code=404, detail="Conversation not found")
        else:
            # Create new conversation
            conversation_id = str(uuid.uuid4())
            conversation = ChatConversation(conversation_id=conversation_id)
            db.add(conversation)
            db.commit()
            db.refresh(conversation)

        # Save user message
        user_message = ChatMessage(
            conversation_id=conversation.conversation_id,
            role="user",
            content=request.message
        )
        db.add(user_message)
        db.commit()

        # Get chat history for context
        messages = db.query(ChatMessage).filter(
            ChatMessage.conversation_id == conversation.conversation_id
        ).order_by(ChatMessage.timestamp).all()

        # Initialize Claude chat service
        claude_service = ClaudeChatService(db)
        
        # Get response from Claude with MCP tools
        assistant_response = await claude_service.get_chat_response(
            message=request.message,
            conversation_history=messages[:-1]  # Exclude the just-added user message
        )

        # Save assistant response
        assistant_message = ChatMessage(
            conversation_id=conversation.conversation_id,
            role="assistant",
            content=assistant_response
        )
        db.add(assistant_message)
        db.commit()

        return ChatResponse(
            response=assistant_response,
            conversation_id=conversation.conversation_id
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")

@router.get("/history", response_model=ChatHistoryResponse)
async def get_chat_history(db: Session = Depends(get_db)):
    """Get the most recent chat conversation history."""
    try:
        # Get the most recent conversation
        conversation = db.query(ChatConversation).order_by(
            desc(ChatConversation.updated_at)
        ).first()

        if not conversation:
            # Return empty history if no conversations exist
            return ChatHistoryResponse(
                conversation_id="",
                messages=[]
            )

        # Get messages for this conversation
        messages = db.query(ChatMessage).filter(
            ChatMessage.conversation_id == conversation.conversation_id
        ).order_by(ChatMessage.timestamp).all()

        message_responses = [
            ChatMessageResponse(
                id=str(msg.id),
                role=msg.role,
                content=msg.content,
                timestamp=msg.timestamp
            )
            for msg in messages
        ]

        return ChatHistoryResponse(
            conversation_id=conversation.conversation_id,
            messages=message_responses
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving chat history: {str(e)}")

@router.delete("/history")
async def clear_chat_history(db: Session = Depends(get_db)):
    """Clear all chat conversation history."""
    try:
        # Delete all conversations (messages will be deleted due to cascade)
        db.query(ChatConversation).delete()
        db.commit()
        
        return {"message": "Chat history cleared successfully"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing chat history: {str(e)}")