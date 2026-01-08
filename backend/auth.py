from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session, select
from backend.database import get_session
from backend.models import User

# Secret key (in production this should be in .env)
SECRET_KEY = "byte_super_secret_key_change_me"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7 # 7 days
import bcrypt
# Monkey patch for passlib 1.7.4 compatibility with bcrypt 4.0+
if not hasattr(bcrypt, '__about__'):
    # Dynamically create an object that mocks the __about__ module
    import types
    bcrypt.__about__ = types.SimpleNamespace(__version__=bcrypt.__version__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")




def verify_password(plain_password, hashed_password):
    try:
        # Use bcrypt directly to have full control over the 72-byte limit
        import bcrypt
        
        # Encode password to bytes
        password_bytes = plain_password.encode('utf-8')
        
        print(f"DEBUG: Input password length: {len(password_bytes)} bytes")
        
        # Bcrypt has a 72-byte limit - truncate if necessary
        if len(password_bytes) > 72:
            print(f"DEBUG: Password is {len(password_bytes)} bytes. Truncating to 72 bytes.")
            password_bytes = password_bytes[:72]
        
        print(f"DEBUG: About to verify password of length {len(password_bytes)} bytes")
        
        # Encode the hash to bytes if it's a string
        if isinstance(hashed_password, str):
            hash_bytes = hashed_password.encode('utf-8')
        else:
            hash_bytes = hashed_password
        
        # Use bcrypt directly
        result = bcrypt.checkpw(password_bytes, hash_bytes)
        print(f"DEBUG: Verification result: {result}")
        return result
        
    except Exception as e:
        print(f"DEBUG: Error in verify_password: {type(e).__name__}: {e}")
        return False


def get_password_hash(password):
    # Use bcrypt directly for consistency
    import bcrypt
    
    # Truncate to 72 bytes for bcrypt compatibility
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
    
    # Generate salt and hash
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    
    # Return as string for database storage
    return hashed.decode('utf-8')

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(token: str = Depends(oauth2_scheme), session: Session = Depends(get_session)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    statement = select(User).where(User.email == email)
    user = session.exec(statement).first()
    if user is None:
        raise credentials_exception
    return user
