
from jose import jwt
from passlib.context import CryptContext
from datetime import datetime
from .constants import SECRET_KEY,ALGORITHM
from .models import User
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

from datetime import timedelta

from .database import get_db


def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> bool:
    try:
        # Perform verification logic here
        # For example, you can decode and verify the token using a library like PyJWT

        print(f'token == > {token}')
        decoded_token = jwt.decode(token, SECRET_KEY, algorithms=ALGORITHM)
        print(f'decoded_token == > {decoded_token}')

        # You can also perform additional checks such as checking the token expiry or checking against a database
        # For example:
        # Check token expiry

        if datetime.utcnow() > datetime.fromtimestamp(decoded_token.get('exp')):
            return False
        
        # Check against a database
        print(f'user == > ',decoded_token.get('sub'))
        try:
            db = next(get_db())
            user = get_user(db, decoded_token.get('sub'))
        except Exception as error:
            print("An error occurred:", error) # An error occurred: name 'x' is not defined
        # user = User.get_user_by_id(decoded_token.get('sub'))
        print('user --> ',user)
        if not user :
            print('user --> ','false')
            return False
        print('user --> ','true')
        
        return True
    except jwt.JWTError:
        return False

def get_password_hash(password):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_user(db, username: str):
    user = db.query(User).filter(User.username == username).first()
    return user

def authenticate_user(db, username: str, password: str):
    user = get_user(db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user