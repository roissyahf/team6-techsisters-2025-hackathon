"""career_compass schema

Revision ID: career_compass_init
Revises:
Create Date: 2025-11-09
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "career_compass_init"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Drop legacy books table if present
    op.execute("DROP TABLE IF EXISTS books CASCADE")

    # --- Create ENUM only if it doesn't exist (idempotent) ---
    op.execute("""
    DO $$
    BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'question_type') THEN
            CREATE TYPE question_type AS ENUM ('single','multi','scale','text','boolean','number');
        END IF;
    END$$;
    """)

    # IMPORTANT: use create_type=False on the column so it won't try to recreate it
    qtype = postgresql.ENUM(
        "single", "multi", "scale", "text", "boolean", "number",
        name="question_type",
        create_type=False  # <-- prevents auto CREATE TYPE during table creation
    )

    # categories
    op.create_table(
        "categories",
        sa.Column("id", sa.BigInteger, primary_key=True),
        sa.Column("name", sa.Text, nullable=False, unique=True),
        sa.Column("description", sa.Text),
        sa.Column("position", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    # questions
    op.create_table(
        "questions",
        sa.Column("id", sa.BigInteger, primary_key=True),
        sa.Column("category_id", sa.BigInteger, sa.ForeignKey("categories.id", ondelete="CASCADE"), nullable=False),
        sa.Column("prompt", sa.Text, nullable=False),
        sa.Column("type", qtype, nullable=False),  # uses existing enum, won't try to create it
        sa.Column("is_required", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("position", sa.Integer, nullable=False, server_default="0"),
        sa.Column("meta", postgresql.JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_questions_category_position", "questions", ["category_id", "position"])

    # choices
    op.create_table(
        "choices",
        sa.Column("id", sa.BigInteger, primary_key=True),
        sa.Column("question_id", sa.BigInteger, sa.ForeignKey("questions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("label", sa.Text, nullable=False),
        sa.Column("value", sa.Text, nullable=False),
        sa.Column("position", sa.Integer, nullable=False, server_default="0"),
        sa.Column("meta", postgresql.JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("question_id", "value", name="uq_choices_question_value"),
    )
    op.create_index("ix_choices_question_position", "choices", ["question_id", "position"])

    # respondents
    op.create_table(
        "respondents",
        sa.Column("id", sa.BigInteger, primary_key=True),
        sa.Column("external_user_id", sa.Text, unique=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    # response_sessions
    op.create_table(
        "response_sessions",
        sa.Column("id", sa.BigInteger, primary_key=True),
        sa.Column("respondent_id", sa.BigInteger, sa.ForeignKey("respondents.id", ondelete="SET NULL")),
        sa.Column("status", sa.Text, nullable=False, server_default=sa.text("'in_progress'")),
        sa.Column("started_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("completed_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("meta", postgresql.JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
    )
    op.create_index("ix_response_sessions_respondent", "response_sessions", ["respondent_id"])

    # answers
    op.create_table(
        "answers",
        sa.Column("id", sa.BigInteger, primary_key=True),
        sa.Column("response_session_id", sa.BigInteger, sa.ForeignKey("response_sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("question_id", sa.BigInteger, sa.ForeignKey("questions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("choice_id", sa.BigInteger, sa.ForeignKey("choices.id", ondelete="SET NULL")),
        sa.Column("multi_choice_ids", postgresql.ARRAY(sa.BigInteger)),
        sa.Column("text_value", sa.Text),
        sa.Column("number_value", sa.Numeric(10, 2)),
        sa.Column("boolean_value", sa.Boolean),
        sa.Column("meta", postgresql.JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("response_session_id", "question_id", name="uq_answers_session_question"),
    )
    op.create_index("ix_answers_session", "answers", ["response_session_id"])
    op.create_index("ix_answers_question", "answers", ["question_id"])
    op.create_index("ix_answers_choice", "answers", ["choice_id"])


def downgrade():
    op.drop_index("ix_answers_choice", table_name="answers")
    op.drop_index("ix_answers_question", table_name="answers")
    op.drop_index("ix_answers_session", table_name="answers")
    op.drop_table("answers")

    op.drop_index("ix_response_sessions_respondent", table_name="response_sessions")
    op.drop_table("response_sessions")

    op.drop_table("respondents")

    op.drop_index("ix_choices_question_position", table_name="choices")
    op.drop_table("choices")

    op.drop_index("ix_questions_category_position", table_name="questions")
    op.drop_table("questions")

    op.drop_table("categories")

    # Drop ENUM last (guarded)
    op.execute("DROP TYPE IF EXISTS question_type")
