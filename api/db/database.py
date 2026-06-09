import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from dotenv import load_dotenv

load_dotenv()

# pull connection details from env vars
DB_URL = (
    f"postgresql+asyncpg://"
    f"{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}"
    f"@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}"
    f"/{os.getenv('POSTGRES_DB')}"
)

# echo=False to avoid logging sensitive info in prod
engine = create_async_engine(DB_URL, echo=False)

# this is what we'd use accross the app to interact with the db
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

async def get_db():
    # fastapi dependency to get a db session for each request
    async with SessionLocal() as session:
        yield session