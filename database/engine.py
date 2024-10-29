from environs import Env
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

env = Env()
env.read_env()

engine = create_async_engine(env('DB_POSTGRESQL'), echo=True)
session_maker = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
