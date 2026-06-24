"""Seed demo decks and cards. Run after auth-svc seed via: python -m deck_svc.seed"""
import asyncio
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import select

from deck_svc.database import AsyncSessionLocal
from deck_svc.models import Card, Deck

DEMO_USER_ID_FILE = "/tmp/demo_user_id"
DEMO_EMAIL = "demo@example.com"


def _new_fsrs_state(due_offset_days: int = 0) -> dict[str, Any]:
    due = datetime.now(UTC) + timedelta(days=due_offset_days)
    return {
        "stability": 1.0,
        "difficulty": 5.0,
        "due_at": due.isoformat(),
        "last_review": None,
        "reps": 0,
        "lapses": 0,
        "state": "new" if due_offset_days == 0 else "review",
    }


AWS_CARDS = [
    ("What does S3 stand for?", "Simple Storage Service"),
    ("What is an EC2 instance?", "A virtual server in the AWS cloud"),
    ("What is the default S3 storage class?", "S3 Standard"),
    ("What is AWS IAM?", "Identity and Access Management — controls access to AWS services"),
    ("What is a VPC?", "Virtual Private Cloud — isolated network in AWS"),
    ("What is an Availability Zone?", "Isolated data center location within an AWS Region"),
    ("What is CloudFront?", "AWS CDN service for low-latency content delivery"),
    ("What is RDS?", "Relational Database Service — managed SQL databases on AWS"),
    ("What is Lambda?", "Serverless compute service that runs code in response to events"),
    ("What is an ELB?", "Elastic Load Balancer — distributes traffic across targets"),
    ("What is Route 53?", "AWS scalable DNS web service"),
    ("What is SQS?", "Simple Queue Service — managed message queue"),
    ("What is SNS?", "Simple Notification Service — pub/sub messaging"),
    ("What is ECS?", "Elastic Container Service — run Docker containers on AWS"),
    ("What is the AWS shared responsibility model?", "AWS manages security OF the cloud; customers manage security IN the cloud"),
]

MATH_CARDS = [
    ("What is the quadratic formula?", "x = (-b ± √(b²-4ac)) / 2a"),
    ("What is the Pythagorean theorem?", "a² + b² = c²"),
    ("What is the area of a circle?", "A = πr²"),
    ("What is the circumference of a circle?", "C = 2πr"),
    ("What is the slope formula?", "m = (y₂-y₁) / (x₂-x₁)"),
    ("What is the distance formula?", "d = √((x₂-x₁)² + (y₂-y₁)²)"),
    ("What is sin(30°)?", "0.5"),
    ("What is cos(60°)?", "0.5"),
    ("What is the derivative of xⁿ?", "nxⁿ⁻¹"),
    ("What is ∫xⁿ dx?", "xⁿ⁺¹ / (n+1) + C"),
]


async def main() -> None:
    # Read the demo user ID from auth-svc seed output or use a fixed UUID for demo
    demo_user_id = uuid.UUID("00000000-0000-0000-0000-000000000001")

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Deck).where(Deck.user_id == demo_user_id))
        if result.first():
            print("Demo decks already exist, skipping.")
            return

        # AWS deck — half reviewed
        aws_deck = Deck(user_id=demo_user_id, name="AWS SAA Practice")
        db.add(aws_deck)
        await db.flush()

        for i, (front, back) in enumerate(AWS_CARDS):
            if i < 8:
                # Already reviewed — some due today, some future
                offset = 0 if i % 2 == 0 else 3
                state = {
                    "stability": 5.0 + i,
                    "difficulty": 4.5,
                    "due_at": (datetime.now(UTC) + timedelta(days=offset)).isoformat(),
                    "last_review": (datetime.now(UTC) - timedelta(days=1)).isoformat(),
                    "reps": i + 1,
                    "lapses": 0,
                    "state": "review",
                }
            else:
                state = _new_fsrs_state(0)
            db.add(Card(deck_id=aws_deck.id, front=front, back=back, fsrs_state=state))

        # Math deck — all new
        math_deck = Deck(user_id=demo_user_id, name="Bagrut Math")
        db.add(math_deck)
        await db.flush()

        for front, back in MATH_CARDS:
            db.add(Card(deck_id=math_deck.id, front=front, back=back, fsrs_state=_new_fsrs_state(0)))

        await db.commit()
        print(f"Created decks for user {demo_user_id}: AWS SAA Practice (15 cards), Bagrut Math (10 cards)")


if __name__ == "__main__":
    asyncio.run(main())
