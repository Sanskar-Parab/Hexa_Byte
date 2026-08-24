import uuid
from sqlalchemy import String, TypeDecorator


class GUID(TypeDecorator):
    """Portable UUID type that stores as CHAR(36) on SQLite and native UUID on PostgreSQL."""

    impl = String(36)
    cache_ok = True

    def __init__(self):
        super().__init__()

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            from sqlalchemy.dialects.postgresql import UUID as PG_UUID
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        else:
            return dialect.type_descriptor(String(36))

    def process_bind_param(self, value, dialect):
        if value is not None:
            if dialect.name == "postgresql":
                return value
            if isinstance(value, uuid.UUID):
                return str(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            if dialect.name == "postgresql":
                return value
            if not isinstance(value, uuid.UUID):
                return uuid.UUID(value)
        return value
