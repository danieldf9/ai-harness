"""seed_browser_tool

Revision ID: a1907066c1a6
Revises: f8cb67f38fb6
Create Date: 2026-06-10 11:47:49.354460

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1907066c1a6'
down_revision = 'f8cb67f38fb6'
branch_labels = None
depends_on = None

BROWSER_TOOL = {
    "name": "browser_interaction",
    "display_name": "Browser",
    "description": (
        "Interact with a web browser to navigate pages, click elements, fill forms, "
        "evaluate JavaScript, and take screenshots. The browser state is persistent. "
        "CRITICAL INSTRUCTION: You have full ability to interact with JavaScript-heavy "
        "dynamic content, click buttons, fill forms, handle authentication flows, "
        "execute scripts, and take screenshots using this tool. NEVER claim you cannot "
        "do these things. If a user asks you to interact with a website or login, USE THIS TOOL."
    ),
    "in_code_tool_id": "BrowserTool",
    "enabled": True,
}

def upgrade() -> None:
    conn = op.get_bind()

    existing = conn.execute(
        sa.text(
            "SELECT in_code_tool_id FROM tool WHERE in_code_tool_id = :in_code_tool_id"
        ),
        {"in_code_tool_id": BROWSER_TOOL["in_code_tool_id"]},
    ).fetchone()

    if existing:
        conn.execute(
            sa.text("""
                UPDATE tool
                SET name = :name,
                    display_name = :display_name,
                    description = :description
                WHERE in_code_tool_id = :in_code_tool_id
                """),
            BROWSER_TOOL,
        )
    else:
        conn.execute(
            sa.text("""
                INSERT INTO tool (name, display_name, description, in_code_tool_id, enabled)
                VALUES (:name, :display_name, :description, :in_code_tool_id, :enabled)
                """),
            BROWSER_TOOL,
        )


def downgrade() -> None:
    pass
