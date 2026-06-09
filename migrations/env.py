import asyncio
import os
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context
from dotenv import load_dotenv

# pull in our ORM models so alembic knows what tables to create
from api.db.orm import Base

load_dotenv()

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)
    
# this is what alembic compares against to detect schema changes
target_metadata = Base.metadata

# override the url from alembic.ini with our env var config
config.set_main_option(
    "sqlalchemy.url",
    f"postgresql+asyncpg://"
    f"{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}"
    f"@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}"
    f"/{os.getenv('POSTGRES_DB')}"
)

# run migrations in 'offline' mode (without a live connection)
def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()
        
def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()
        
    
# run migrations in 'online' mode (with a live connection)
async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()
    

# entry point for alembic to run the migrations
def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())
    
# determine if we're in offline or online mode and run the appropriate function
if context.is_offline_mode():
    run_migrations_offline()
else:   
    run_migrations_online()
    
    