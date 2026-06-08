import asyncio
from sqlalchemy import text
from onyx.db.engine.async_sql_engine import get_sqlalchemy_async_engine
from onyx.db.models import User
from onyx.auth.schemas import UserRole

async def main():
    async_engine = get_sqlalchemy_async_engine()
    async with async_engine.begin() as conn:
        # Check what the actual DB has for a test user
        await conn.execute(User.__table__.insert().values(
            email="test_insert@example.com",
            hashed_password="foo",
            role=UserRole.BASIC
        ))
        
        result = await conn.execute(
            text("SELECT role FROM \"user\" WHERE email = 'test_insert@example.com'")
        )
        role = result.scalar()
        print("Inserted raw role via SQLAlchemy Core with UserRole.BASIC:", role)

        # What if we insert via ORM
        from sqlalchemy.orm import sessionmaker
        from sqlalchemy.ext.asyncio import AsyncSession
        async_session_maker = sessionmaker(
            async_engine, class_=AsyncSession, expire_on_commit=False
        )
        async with async_session_maker() as session:
            new_user = User(
                email="test_insert_orm@example.com",
                hashed_password="foo",
                role=UserRole.BASIC
            )
            session.add(new_user)
            await session.commit()
            
            result2 = await session.execute(
                text("SELECT role FROM \"user\" WHERE email = 'test_insert_orm@example.com'")
            )
            role2 = result2.scalar()
            print("Inserted raw role via SQLAlchemy ORM with UserRole.BASIC:", role2)

        # Cleanup
        await conn.execute(User.__table__.delete().where(User.__table__.c.email.in_(["test_insert@example.com", "test_insert_orm@example.com"])))

asyncio.run(main())
