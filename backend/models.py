from typing import Optional, List
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, JSON

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True)
    name: str = Field(default="User")
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
    thinking: Optional[str] = Field(default=None)  # Store thinking/reasoning content
    tool_invocations: List[dict] = Field(default=[], sa_column=Column(JSON))  # Store full tool results [{name, args, result, status}]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    user: Optional[User] = Relationship(back_populates="logs")
    thread: Optional[ChatThread] = Relationship(back_populates="logs")


# --- Tool History Models ---

class ToolHistory(SQLModel, table=True):
    """Base model for storing tool usage history"""
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    tool_type: str = Field(index=True)  # url_checker | code_checker | fake_news | quiz
    input_data: str  # The input provided by user
    output_data: str  # The result/analysis
    extra_data: dict = Field(default={}, sa_column=Column(JSON))  # Additional data (renamed from metadata)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class QuizAttempt(SQLModel, table=True):
    """Store quiz attempts and scores"""
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    quiz_category: str  # phishing | malware | social_engineering | upi_fraud | cyber_laws
    total_questions: int
    correct_answers: int
    score_percentage: float
    answers: List[dict] = Field(default=[], sa_column=Column(JSON))  # [{question_id, selected, correct, is_correct}]
    time_taken_seconds: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
