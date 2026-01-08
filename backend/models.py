from typing import Optional, List
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, JSON

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True)
    password_hash: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    profile: Optional["UserSecurityProfile"] = Relationship(back_populates="user")
    logs: List["ConversationLog"] = Relationship(back_populates="user")
    threads: List["ChatThread"] = Relationship(back_populates="user")

class UserSecurityProfile(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    
    technical_level: str = Field(default="non-technical") # non-technical | developer
    common_threats: List[str] = Field(default=[], sa_column=Column(JSON))
    platforms_used: List[str] = Field(default=[], sa_column=Column(JSON))
    past_incidents: List[str] = Field(default=[], sa_column=Column(JSON))
    explanation_preference: str = Field(default="simple") # simple | detailed
    
    user: Optional[User] = Relationship(back_populates="profile")

class ChatThread(SQLModel, table=True):
    id: str = Field(primary_key=True) # UUID
    user_id: int = Field(foreign_key="user.id")
    title: str = Field(default="New Chat")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    user: Optional[User] = Relationship(back_populates="threads")
    logs: List["ConversationLog"] = Relationship(back_populates="thread")

class ConversationLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    thread_id: str = Field(foreign_key="chatthread.id")
    role: str # user | assistant
    content: str
    mode: str = Field(default="simple") # simple | turbo
    tool_calls: List[str] = Field(default=[], sa_column=Column(JSON))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    user: Optional[User] = Relationship(back_populates="logs")
    thread: Optional[ChatThread] = Relationship(back_populates="logs")
