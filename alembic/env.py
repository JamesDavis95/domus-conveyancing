import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/..")

from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

# Import database config and models
from database_config import engine, Base
from models import *  # Load all model classes to register with Base

config = context.config
fileConfig(config.config_file_name)

# Load DB URL from env if set
db_url = os.getenv("DATABASE_URL")
if db_url:
    config.set_main_option("sqlalchemy.url", db_url)

# Set target metadata from Base
target_metadata = Base.metadata

def run_migrations_offline():
    context.configure(url=config.get_main_option("sqlalchemy.url"), literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection)
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
