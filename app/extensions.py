# extensions.py
from sqlalchemy import MetaData
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# OPTIONAL: only if you'll send emails (password reset/confirm):
# from flask_mailman import Mail

# Deterministic names for indexes/constraints → cleaner Alembic diffs
naming_convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

db = SQLAlchemy(metadata=MetaData(naming_convention=naming_convention))
migrate = Migrate()

# OPTIONAL (only if you enabled email flows in config):
# mail = Mail()
