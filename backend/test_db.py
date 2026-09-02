from app.core.database import engine
from sqlalchemy import text

try:
    with engine.connect() as connection:
        result = connection.execute(text("SELECT version();"))
        print("✅ Connected to PostgreSQL!")
        print(result.scalar())

except Exception as e:
    print("❌ Connection failed!")
    print(e)