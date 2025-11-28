from datetime import datetime
from .extensions import db
from sqlalchemy.dialects import postgresql

question_type_enum = postgresql.ENUM(
    "single", "multi", "scale", "text", "boolean", "number",
    name="question_type",
    create_type=False,   # important: don't auto-create from models
    inherit_schema=False
)

class TimestampMixin:
    created_at = db.Column(db.DateTime(timezone=True), default=db.func.now(), nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), default=db.func.now(), onupdate=db.func.now(), nullable=False)

class Category(TimestampMixin, db.Model):
    __tablename__ = "categories"
    id = db.Column(db.BigInteger, primary_key=True)
    name = db.Column(db.Text, unique=True, nullable=False)
    description = db.Column(db.Text)
    position = db.Column(db.Integer, nullable=False, server_default="0")
    questions = db.relationship("Question", back_populates="category", cascade="all, delete-orphan")
    technical_questions = db.relationship("TechnicalQuestion",back_populates="category",cascade="all, delete-orphan")

class Question(TimestampMixin, db.Model):
    __tablename__ = "questions"
    id = db.Column(db.BigInteger, primary_key=True)
    category_id = db.Column(db.BigInteger, db.ForeignKey("categories.id", ondelete="CASCADE"), nullable=False)
    prompt = db.Column(db.Text, nullable=False)
    type = db.Column(question_type_enum, nullable=False)
    is_required = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))
    position = db.Column(db.Integer, nullable=False, server_default="0")
    meta = db.Column(postgresql.JSONB, nullable=False, server_default=db.text("'{}'::jsonb"))

    category = db.relationship("Category", back_populates="questions")
    choices = db.relationship("Choice", back_populates="question", cascade="all, delete-orphan")

class TechnicalQuestion(TimestampMixin, db.Model):
    __tablename__ = "technical_questions"

    id = db.Column(db.BigInteger, primary_key=True)
    category_id = db.Column(
        db.BigInteger,
        db.ForeignKey("categories.id", ondelete="CASCADE"),
        nullable=False,
    )
    job_roles_id = db.Column(
        db.BigInteger,
        db.ForeignKey("job_roles.id", ondelete="SET NULL"),
        nullable=True,
    )
    prompt = db.Column(db.Text, nullable=False)
    type = db.Column(question_type_enum, nullable=False)  # reuse same ENUM
    is_required = db.Column(
        db.Boolean,
        nullable=False,
        server_default=db.text("false"),
    )
    position = db.Column(
        db.Integer,
        nullable=False,
        server_default="0",
    )
    meta = db.Column(
        postgresql.JSONB,
        nullable=False,
        server_default=db.text("'{}'::jsonb"),
    )

    category = db.relationship("Category", back_populates="technical_questions")
    job_role = db.relationship("JobRole", back_populates="technical_questions")
    choices = db.relationship(
        "TechnicalChoice",
        back_populates="question",
        cascade="all, delete-orphan",
    )

class TechnicalChoice(TimestampMixin, db.Model):
    __tablename__ = "technical_choices"

    id = db.Column(db.BigInteger, primary_key=True)
    question_id = db.Column(
        db.BigInteger,
        db.ForeignKey("technical_questions.id", ondelete="CASCADE"),
        nullable=False,
    )
    label = db.Column(db.Text, nullable=False)
    value = db.Column(db.Text, nullable=False)
    position = db.Column(
        db.Integer,
        nullable=False,
        server_default="0",
    )
    meta = db.Column(
        postgresql.JSONB,
        nullable=False,
        server_default=db.text("'{}'::jsonb"),
    )

    question = db.relationship("TechnicalQuestion", back_populates="choices")

    __table_args__ = (
        db.UniqueConstraint(
            "question_id",
            "value",
            name="uq_technical_choices_question_value",
        ),
    )
    

class Choice(TimestampMixin, db.Model):
    __tablename__ = "choices"
    id = db.Column(db.BigInteger, primary_key=True)
    question_id = db.Column(db.BigInteger, db.ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    label = db.Column(db.Text, nullable=False)
    value = db.Column(db.Text, nullable=False)
    position = db.Column(db.Integer, nullable=False, server_default="0")
    meta = db.Column(postgresql.JSONB, nullable=False, server_default=db.text("'{}'::jsonb"))

    question = db.relationship("Question", back_populates="choices")

    __table_args__ = (db.UniqueConstraint("question_id", "value", name="uq_choices_question_value"),)

class Respondent(db.Model):
    __tablename__ = "respondents"
    id = db.Column(db.BigInteger, primary_key=True)
    external_user_id = db.Column(db.Text, unique=True)
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now(), nullable=False)

class ResponseSession(db.Model):
    __tablename__ = "response_sessions"
    id = db.Column(db.BigInteger, primary_key=True)
    respondent_id = db.Column(db.BigInteger, db.ForeignKey("respondents.id", ondelete="SET NULL"))
    status = db.Column(db.Text, nullable=False, server_default=db.text("'in_progress'"))
    started_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now(), nullable=False)
    completed_at = db.Column(db.DateTime(timezone=True))
    meta = db.Column(postgresql.JSONB, nullable=False, server_default=db.text("'{}'::jsonb"))

class Answer(db.Model):
    __tablename__ = "answers"
    id = db.Column(db.BigInteger, primary_key=True)
    response_session_id = db.Column(db.BigInteger, db.ForeignKey("response_sessions.id", ondelete="CASCADE"), nullable=False)
    question_id = db.Column(db.BigInteger, db.ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    choice_id = db.Column(db.BigInteger, db.ForeignKey("choices.id", ondelete="SET NULL"))
    multi_choice_ids = db.Column(postgresql.ARRAY(db.BigInteger))
    text_value = db.Column(db.Text)
    number_value = db.Column(db.Numeric(10, 2))
    boolean_value = db.Column(db.Boolean)
    meta = db.Column(postgresql.JSONB, nullable=False, server_default=db.text("'{}'::jsonb"))
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now(), nullable=False)

    __table_args__ = (db.UniqueConstraint("response_session_id", "question_id", name="uq_answers_session_question"),)

class JobRole(TimestampMixin, db.Model):
    __tablename__ = "job_roles"
    id = db.Column(db.BigInteger, primary_key=True)
    title = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text)
    
    # Relationships
    courses = db.relationship("Course", back_populates="job_role", cascade="all, delete-orphan")
    live_jobs = db.relationship("LiveJob", back_populates="job_role", cascade="all, delete-orphan")
    technical_questions = db.relationship("TechnicalQuestion", back_populates="job_role")

class Course(TimestampMixin, db.Model):
    __tablename__ = "courses"
    id = db.Column(db.BigInteger, primary_key=True)
    title = db.Column(db.Text, nullable=False)
    course_title = db.Column(db.Text)  # Alternative/additional title field
    description = db.Column(db.Text)
    location = db.Column(db.Text)
    job_roles_id = db.Column(db.BigInteger, db.ForeignKey("job_roles.id", ondelete="CASCADE"), nullable=False)
    timeline = db.Column(db.Text)
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    
    # New fields
    platform = db.Column(db.Text)
    skills = db.Column(postgresql.JSONB, nullable=False, server_default=db.text("'[]'::jsonb"))
    rating = db.Column(db.Numeric(3, 2))  # e.g., 4.9
    reviewcount = db.Column(db.Integer, default=0)
    level = db.Column(db.Text)  # e.g., "beginner"
    duration = db.Column(db.Text)  # e.g., "1 - 3 Months"
    certificatetype = db.Column(db.Text)  # e.g., "Course"
    crediteligibility = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="SET NULL"), nullable=True)
    
    # Relationships
    job_role = db.relationship("JobRole", back_populates="courses")
    user = db.relationship("User", foreign_keys=[user_id])

class LiveJob(TimestampMixin, db.Model):
    __tablename__ = "live_jobs"
    id = db.Column(db.BigInteger, primary_key=True)
    title = db.Column(db.Text, nullable=False)
    location = db.Column(db.Text)
    description = db.Column(db.Text)
    salary = db.Column(db.Text)
    start_date = db.Column(db.Date)
    job_roles_id = db.Column(db.BigInteger, db.ForeignKey("job_roles.id", ondelete="CASCADE"), nullable=False)
    
    # Relationships
    job_role = db.relationship("JobRole", back_populates="live_jobs")

class Country(TimestampMixin, db.Model):
    __tablename__ = "countries"
    id = db.Column(db.BigInteger, primary_key=True)
    name = db.Column(db.Text, unique=True, nullable=False)
    code = db.Column(db.String(2), unique=True, nullable=False)  # ISO 3166-1 alpha-2 code
    code3 = db.Column(db.String(3), unique=True, nullable=True)  # ISO 3166-1 alpha-3 code

# --- Flask-Security-Too models (append below your existing models) ---
from flask_security import UserMixin, RoleMixin
from sqlalchemy import Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship

# Association table between users and roles
roles_users = db.Table(
    "roles_users",
    db.Column("user_id", Integer, db.ForeignKey("user.id"), primary_key=True),
    db.Column("role_id", Integer, db.ForeignKey("role.id"), primary_key=True),
)

class Role(db.Model, RoleMixin):
    __tablename__ = "role"
    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(80), unique=True, nullable=False)
    description = db.Column(String(255))

class User(db.Model, UserMixin):
    __tablename__ = "user"
    id = db.Column(Integer, primary_key=True)
    email = db.Column(String(255), unique=True, nullable=False, index=True)
    password = db.Column(String(255), nullable=False)
    active = db.Column(Boolean(), nullable=False, default=True)
    fs_uniquifier = db.Column(String(64), unique=True, nullable=False)
    
    # User profile fields
    firstname = db.Column(String(100), nullable=True)
    lastname = db.Column(String(100), nullable=True)
    country_id = db.Column(db.BigInteger, db.ForeignKey("countries.id", ondelete="SET NULL"), nullable=True)
    
    # Suggested/Assigned Job Role
    job_role_id = db.Column(db.BigInteger, db.ForeignKey("job_roles.id", ondelete="SET NULL"), nullable=True)

    # Optional but useful if SECURITY_TRACKABLE=True
    last_login_at = db.Column(DateTime)
    current_login_at = db.Column(DateTime)
    last_login_ip = db.Column(String(100))
    current_login_ip = db.Column(String(100))
    login_count = db.Column(Integer, default=0)
    confirmed_at = db.Column(DateTime)

    roles = relationship("Role", secondary=roles_users, backref="users")
    job_role = relationship("JobRole", foreign_keys=[job_role_id])
    country = relationship("Country", foreign_keys=[country_id])

