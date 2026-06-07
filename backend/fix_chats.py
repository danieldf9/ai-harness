import re
import os
import sys

# Add backend to path so we can import onyx
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from onyx.db.engine.sql_engine import get_session_with_current_tenant, SqlEngine
from onyx.db.models import ChatSession
from sqlalchemy import select

def main():
    SqlEngine.init_engine(pool_size=1, max_overflow=1)
    with get_session_with_current_tenant() as db_session:
        chat_sessions = db_session.scalars(select(ChatSession)).all()
        count = 0
        for session in chat_sessions:
            if session.description and ('<thought>' in session.description.lower() or '<think>' in session.description.lower()):
                new_desc = re.sub(r'<(?:thought|think)>.*?(?:</(?:thought|think)>|$)', '', session.description, flags=re.DOTALL | re.IGNORECASE).strip().strip('"')
                session.description = new_desc
                count += 1
        db_session.commit()
        print(f"Fixed {count} chat sessions.")

if __name__ == "__main__":
    main()
