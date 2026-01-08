from langchain_core.tools import tool
from sqlmodel import Session, select
from backend.database import engine
from backend.models import User, UserSecurityProfile
from typing import Optional

@tool
def update_user_security_profile(
    user_id: str,
    technical_level: Optional[str] = None,
    new_threat: Optional[str] = None,
    new_incident: Optional[str] = None,
    explanation_preference: Optional[str] = None
) -> str:
    """
    Updates the user's permanent security profile (long-term memory).
    Use this when the user mentions important context that should be remembered forever.
    
    Args:
        user_id: The ID of the user (passed in state)
        technical_level: 'non-technical' or 'developer'
        new_threat: A specific threat the user is concerned about (e.g., "phishing", "ransomware")
        new_incident: A past security incident the user experienced (e.g., "hacked via email")
        explanation_preference: 'simple' or 'detailed'
    """
    try:
        with Session(engine) as session:
            # Find user
            # Assuming user_id is the string ID
            statement = select(User).where(User.id == int(user_id))
            user = session.exec(statement).first()
            
            if not user:
                return "Error: User not found."
            
            # Get or create profile
            if not user.profile:
                profile = UserSecurityProfile(user_id=user.id)
                session.add(profile)
            else:
                profile = user.profile
            
            updates = []
            
            if technical_level:
                profile.technical_level = technical_level
                updates.append(f"Level -> {technical_level}")
                
            if new_threat:
                if not profile.common_threats:
                    profile.common_threats = []
                # Simple append, no dup check for now (or basic check)
                if new_threat not in profile.common_threats:
                    # SQLModel JSON column handling can be tricky, reassigning list helps
                    current_threats = list(profile.common_threats)
                    current_threats.append(new_threat)
                    profile.common_threats = current_threats
                    updates.append(f"Added threat: {new_threat}")
            
            if new_incident:
                if not profile.past_incidents:
                    profile.past_incidents = []
                current_incidents = list(profile.past_incidents)
                current_incidents.append(new_incident)
                profile.past_incidents = current_incidents
                updates.append(f"Added incident: {new_incident}")
                
            if explanation_preference:
                profile.explanation_preference = explanation_preference
                updates.append(f"Preference -> {explanation_preference}")
            
            session.add(profile)
            session.commit()
            session.refresh(profile)
            
            return f"Successfully updated profile: {', '.join(updates)}"
            
    except Exception as e:
        return f"Error updating profile: {str(e)}"
