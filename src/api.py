from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete, update, func
from datetime import datetime, timedelta

from src.models import User, Image
from src.schemas import UserCreate, ImageCreate

maxBytesPerClientHourly = 1 * 1024 * 1024
maxFilesPerClientDaily = 50


async def get_user_by_email(db: AsyncSession, email: str):
    result = await db.execute(select(User).filter(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, id: int):
    result = await db.execute(select(User).filter(User.id == id))
    return result.scalar_one_or_none()


async def create_user(db: AsyncSession, user: UserCreate):
    db_user = User(email=user.email, tenant=user.tenant)
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


async def create_user_image(
    db: AsyncSession, user_id: int, image: ImageCreate
):
    db_image = Image(user_id=user_id, filename=image.filename, data=image.data)
    db.add(db_image)
    await db.commit()
    await db.refresh(db_image)
    return db_image


async def get_user_images(db: AsyncSession, tenant: str):
    # result = await db.execute(select(Image).filter(Image.user_id == user_id))
    result = await db.execute(
        select(Image).join(User.images).filter(User.tenant == tenant)
    )
    return result.scalars().all()


async def get_user_images_by_email(db: AsyncSession, user_email: int):
    result = await db.execute(
        select(Image).join(User.images).filter(User.email == user_email)
    )
    return result.scalars().all()


async def get_image_by_id(db: AsyncSession, user_id: int, image_id: int):
    result = await db.execute(
        select(Image).filter(Image.id == image_id, Image.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def delete_image_by_id(
    db: AsyncSession, user_id: int, image_id: int
) -> bool:
    result = await db.execute(
        delete(Image).where(Image.user_id == user_id, Image.id == image_id)
    )
    await db.commit()
    return result.rowcount == 1


async def update_image_by_id(
    db: AsyncSession, user_id: int, image_id: int, filename: str
) -> bool:
    result = await db.execute(
        update(Image)
        .values(filename=filename)
        .where(Image.user_id == user_id, Image.id == image_id)
    )
    await db.commit()
    return result.rowcount == 1


async def upload_ratelimiter(db: AsyncSession, user_id: int) -> bool:
    """Returns bool that represents an allowance to
    upload for that user in this particular time"""
    return not await isRateLimitedBySize(
        db, user_id
    ) and not await isRateLimitedByAmmount(db, user_id)


async def isRateLimitedBySize(db: AsyncSession, user_id: int) -> bool:
    last_hour_date_time = datetime.now() - timedelta(hours=1)
    result = await db.execute(
        select(func.sum(func.octet_length(Image.data))).filter(
            Image.user_id == user_id, Image.created_at >= last_hour_date_time
        )
    )
    filebytes = result.scalar_one()
    return filebytes and (filebytes >= maxBytesPerClientHourly)


async def isRateLimitedByAmmount(db: AsyncSession, user_id: int) -> bool:
    last_day_date_time = datetime.now() - timedelta(hours=24)
    result = await db.execute(
        select(func.count(Image.id)).filter(
            Image.user_id == user_id, Image.created_at >= last_day_date_time
        )
    )
    nrOfFiles = result.scalar_one()
    return nrOfFiles and (nrOfFiles >= maxFilesPerClientDaily)
