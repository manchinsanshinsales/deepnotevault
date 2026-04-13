"""Pydantic models for the application domain."""

from datetime import datetime
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, Field


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Source(BaseModel):
    """A source citation from a RAG query result."""

    text: str
    page: str | None = None
    filename: str | None = None
    score: float | None = None


class ChatMessage(BaseModel):
    """A single message in a chat conversation."""

    id: str = Field(default_factory=lambda: uuid4().hex)
    role: MessageRole
    content: str
    sources: list[Source] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)


class Document(BaseModel):
    """A document that has been ingested into a notebook."""

    id: str = Field(default_factory=lambda: uuid4().hex)
    filename: str
    file_path: str
    chunk_count: int = 0
    indexed_at: datetime = Field(default_factory=datetime.now)


class Notebook(BaseModel):
    """A notebook containing documents and chat history."""

    id: str = Field(default_factory=lambda: uuid4().hex)
    name: str
    documents: list[Document] = Field(default_factory=list)
    messages: list[ChatMessage] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
