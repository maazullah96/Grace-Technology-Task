from sqlalchemy.orm import Session
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.status import HTTP_401_UNAUTHORIZED
from fastapi import File, UploadFile
from fastapi.responses import StreamingResponse
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import io
from .constants import *
from .auth import *
import os

from .schemas import *

app = FastAPI(debug=True)

import torch
import requests
from PIL import Image

from diffusers import StableDiffusionDepth2ImgPipeline

pipe = StableDiffusionDepth2ImgPipeline.from_pretrained(
    "stabilityai/stable-diffusion-2-depth",
    torch_dtype=torch.float16,
).to("cuda")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

security = HTTPBearer()


@app.post("/signup", response_model=UserResponse)
def signup(user: UserCreate, db: Session = Depends(get_db)):
    db_user = get_user(db, username=user.username)
    if db_user:
        raise HTTPException(
            status_code=400, detail="Username already registered"
        )
    hashed_password = get_password_hash(user.password)
    db_user = User(username=user.username, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@app.post("/login", response_model=Token)
def login(form_data: UserCreate, db: Session = Depends(get_db)):
    print(form_data)
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.post("/uploadfile")
def upload(file: UploadFile = File(...), credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        # Check if the bearer token is present
        print(f'credentials 1 == > {credentials}')
        if not credentials:
            raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Invalid authorization token")

        # Perform additional authorization checks here, such as verifying the token against a database or external service
        print(f'credentials 2 == > {credentials}')
        is_token_valid = verify_token(credentials.credentials)
        print(f'is_token_valid ==> {is_token_valid}')

        if not is_token_valid:
            raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Invalid authorization token")

        allowed_extensions = ['.jpg', '.png']
        file_extension = os.path.splitext(file.filename)[1]

        if file_extension.lower() not in allowed_extensions:
            raise HTTPException(status_code=400, detail="Only JPG or PNG files are allowed")

        contents = file.file.read()

        print(f"file.filename ===> {file.filename}")
        filename = os.path.basename(file.filename)
        with open(filename, 'wb') as f:
            f.write(contents)

        init_image = Image.open(filename)

        base_name, extension = os.path.splitext(filename)

        # Add "converted" to the base name
        converted_name = base_name + "_converted"

        # Concatenate the converted name with the extension
        new_filename = converted_name + extension

        # Print the new filename
        print("new_filename", new_filename)
        try:

            image = pipe(prompt=prompt, image=init_image, negative_prompt=None, strength=0.7).images[0]
            image.save(new_filename)
        except Exception as error:
            print('exception', error)
        print("image_save", new_filename)

        image_bytes = io.BytesIO()
        image.save(image_bytes, format='PNG')
        image_bytes.seek(0)
        print("image_bytes")

    except Exception as error:
        return {"message": error}
    finally:
        file.file.close()

    return StreamingResponse(image_bytes, media_type="image/png")
