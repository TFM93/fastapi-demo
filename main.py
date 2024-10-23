from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from io import BytesIO
from contextlib import asynccontextmanager

import src.models as models
import src.schemas as schemas
import src.api as api
from src.database import async_engine, get_db


# Create tables
@asynccontextmanager
async def lifespan(app: FastAPI):
    async with async_engine.connect() as conn:
        await conn.run_sync(models.Base.metadata.create_all)
        await conn.commit()
    yield
    print("end of lifespan")


app = FastAPI(lifespan=lifespan)


@app.post("/register/", response_model=schemas.UserResp)
async def register_user(
    user: schemas.UserCreate, db: AsyncSession = Depends(get_db)
):
    db_user = await api.get_user_by_email(db, user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="User already registered")
    return await api.create_user(db=db, user=user)


@app.post("/users/{user_id}/upload-image/", response_model=schemas.ImageResp)
async def upload_image(
    user_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    content = await file.read()
    image_data = schemas.ImageCreate(filename=file.filename, data=content)

    # Check if user exists
    db_user = await api.get_user_by_id(db, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    # check ratelimit allowance
    allowed = await api.upload_ratelimiter(db, user_id)
    if not allowed:
        raise HTTPException(status_code=429, detail="User is rate-limited")
    return await api.create_user_image(
        db=db, user_id=user_id, image=image_data
    )


@app.get("/users/{user_id}/images/", response_model=list[schemas.ImageResp])
async def get_images(user_id: int | str, db: AsyncSession = Depends(get_db)):
    try:
        user_id = int(user_id)
        db_user = await api.get_user_by_id(db, user_id)
    except Exception:
        db_user = await api.get_user_by_email(db, user_id)

    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    return await api.get_user_images(db, db_user.tenant)


@app.get("/users/{user_id}/images/{image_id}")
async def get_image(
    user_id: int, image_id: int, db: AsyncSession = Depends(get_db)
):
    # Retrieve the image from the database
    image = await api.get_image_by_id(db, user_id, image_id)
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    # Create a BytesIO stream from the image data
    image_stream = BytesIO(image.data)

    # Return the image as a StreamingResponse
    return StreamingResponse(image_stream, media_type="image/jpeg")


@app.delete("/users/{user_id}/images/{image_id}")
async def del_image(
    user_id: int, image_id: int, db: AsyncSession = Depends(get_db)
):
    deleted = await api.delete_image_by_id(db, user_id, image_id)
    if not deleted:
        return HTTPException(status_code=404, detail="Image not found")
    return


@app.patch("/users/{user_id}/images/{image_id}")
async def update_image(
    user_id: int,
    image_id: int,
    updData: schemas.ImageUpdate,
    db: AsyncSession = Depends(get_db),
):
    updated = await api.update_image_by_id(
        db, user_id, image_id, updData.filename
    )
    if not updated:
        return HTTPException(status_code=404, detail="Image not found")
    return
