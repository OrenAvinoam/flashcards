"""Creates the demo user. Run via: python -m auth_svc.seed"""
import asyncio
import uuid

from argon2 import PasswordHasher
from sqlalchemy import select

from auth_svc.database import AsyncSessionLocal
from auth_svc.models import User

DEMO_EMAIL = "demo@flashcards.local"
DEMO_PASSWORD = "demo1234"
# Fixed UUID so deck-svc seed can reference the same user without a lookup
DEMO_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


async def main() -> None:
    ph = PasswordHasher()
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.email == DEMO_EMAIL))
        if result.scalar_one_or_none():
            print(f"Demo user {DEMO_EMAIL} already exists, skipping.")
            return
        user = User(id=DEMO_USER_ID, email=DEMO_EMAIL, password_hash=ph.hash(DEMO_PASSWORD))
        db.add(user)
        await db.commit()
        print(f"Created demo user: {DEMO_EMAIL}")


if __name__ == "__main__":
    asyncio.run(main())
