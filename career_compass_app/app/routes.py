from flask import Blueprint, request, jsonify, abort, render_template, redirect, url_for, flash, Flask
from .extensions import db
from .models import Category, Question, Choice, Respondent, ResponseSession, Answer,TechnicalQuestion,TechnicalChoice, JobRole, Course, LiveJob, User
from sqlalchemy.exc import IntegrityError
from flask_security import auth_required
import json
import http.client
from datetime import datetime
from flask_login import current_user, login_required
import os
import ast
from dotenv import load_dotenv
from openai import OpenAI
from typing import List, Literal, Dict, Any
from pydantic import BaseModel, Field, ValidationError


# === 1. Define Strict JSON Schema using Pydantic (for Validation and Generation) ===

class QuestionOptions(BaseModel):
    """Defines the four ordinal answer options."""
    A: str = Field(description="Highest alignment score (e.g., Always/Strongly Agree).")
    B: str = Field(description="Medium-High alignment score (e.g., Often/Agree).")
    C: str = Field(description="Medium-Low alignment score (e.g., Sometimes/Neutral).")
    D: str = Field(description="Lowest alignment score (e.g., Rarely/Disagree).")

class DynamicQuestion(BaseModel):
    """Defines the structure for a single assessment question."""
    competency: Literal["A", "B", "C", "D", "E", "F"] = Field(
        description="The primary skill category (A-F) this question assesses. Must be one of A, B, C, D, E, or F."
    )
    competency_name: str = Field(description="The full name of the competency.")
    question_text: str = Field(description="The non-technical, behavioral question text, personalized to the user's persona and focused on their area of interest.")
    options: QuestionOptions

class DynamicAssessment(BaseModel):
    """The root object containing the assessment result."""
    user_context_summary: str = Field(description="A 3-5 word summary of the user's synthesized persona and main interest.")
    questions: List[DynamicQuestion] = Field(
        min_items=6, 
        max_items=6, 
        description="A list containing exactly 6 dynamic questions, each targeting one competency."
    )

# --- 2. Initialize Flask App and Client ---
app = Flask(__name__)
load_dotenv()

# Check for API key and initialize client
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("Warning: OPENAI_API_KEY environment variable not set.")
    pass

client = OpenAI(api_key=api_key)

api = Blueprint("api", __name__)
web = Blueprint("web", __name__)



@web.get("/")
@auth_required() 
def health():
    cats = Category.query.order_by(Category.position.asc(), Category.id.asc()).all()
    qs = Question.query.order_by(Question.category_id.asc(), Question.position.asc()).all()
    user_id = current_user.id
    user = User.query.get(user_id)
    role_id = user.job_role_id
    if not role_id:
        return render_template("front_index.html", categories=cats, questions=qs, user_id=user_id)
    else:
        courses = Course.query.filter_by(user_id=user_id).all()
        now = datetime.now()
        return render_template("dashboard.html",courses=courses, now=now)
    #return {"status": "hello"}


@web.get("/dashboard")
@auth_required() 
def dashboard():
    user_id = current_user.id
    courses = Course.query.filter_by(user_id=user_id).all()
    now = datetime.now()
    return render_template("dashboard.html", courses=courses, now=now)


@web.get("/retake-quiz")
@auth_required() 
def retake_quiz():
    cats = Category.query.order_by(Category.position.asc(), Category.id.asc()).all()
    qs = Question.query.order_by(Question.category_id.asc(), Question.position.asc()).all()
    user_id = current_user.id
    user = User.query.get(user_id)
    role_id = user.job_role_id
    return render_template("front_index.html", categories=cats, questions=qs, user_id=user_id)

@web.get("/loading")
def loader():
    return render_template("loading.html")

@web.get("/base_quiz")
@auth_required() 
def base_quiz():
    return render_template("loading.html", categories=cats)
    #return {"status": "hello"}

# ------- Categories (API) -------

@api.post("/categories")
def create_category():
    data = request.get_json(force=True)
    name = data.get("name")
    if not name:
        abort(400, "name is required")
    cat = Category(name=name, description=data.get("description"), position=data.get("position") or 0)
    db.session.add(cat)
    db.session.commit()
    return jsonify({"id": cat.id, "name": cat.name}), 201

@api.get("/categories")
def list_categories():
    cats = Category.query.order_by(Category.position.asc(), Category.id.asc()).all()
    return jsonify([{"id": c.id, "name": c.name, "description": c.description, "position": c.position} for c in cats])

# ------- Questions (API) -------
@api.post("/questions")
def create_question():
    data = request.get_json(force=True)
    req = ["category_id", "prompt", "type"]
    if any(k not in data for k in req):
        abort(400, "category_id, prompt, type are required")
    q = Question(
        category_id=data["category_id"],
        prompt=data["prompt"],
        type=data["type"],
        is_required=bool(data.get("is_required", False)),
        position=int(data.get("position") or 0),
        meta=data.get("meta") or {},
    )
    db.session.add(q)
    db.session.commit()
    return jsonify({"id": q.id}), 201

@api.get("/questions")
def list_questions():
    qs = Question.query.order_by(Question.category_id.asc(), Question.position.asc()).all()
    out = []
    for q in qs:
        out.append({
            "id": q.id,
            "category_id": q.category_id,
            "prompt": q.prompt,
            "type": q.type,
            "is_required": q.is_required,
            "position": q.position,
        })
    return jsonify(out)

# ------- Choices (API) -------
@api.post("/choices")
def create_choice():
    data = request.get_json(force=True)
    req = ["question_id", "label", "value"]
    if any(k not in data for k in req):
        abort(400, "question_id, label, value are required")
    c = Choice(
        question_id=data["question_id"],
        label=data["label"],
        value=data["value"],
        position=int(data.get("position") or 0),
        meta=data.get("meta") or {},
    )
    db.session.add(c)
    db.session.commit()
    return jsonify({"id": c.id}), 201

@api.get("/choices")
@api.get("/choices/<int:question_id>")
def list_choices(question_id=None):
    query = Choice.query
    if question_id:
        query = query.filter(Choice.question_id == question_id)
    cs = query.order_by(Choice.question_id.asc(), Choice.position.asc()).all()
    return jsonify([{
        "id": c.id, "question_id": c.question_id, "label": c.label, "value": c.value, "position": c.position
    } for c in cs])

# ------- Respondents (API) -------
@api.post("/respondents")
def create_respondent():
    data = request.get_json(force=True)
    ext = data.get("external_user_id")
    r = Respondent(external_user_id=ext) if ext else Respondent()
    db.session.add(r)
    db.session.commit()
    return jsonify({"id": r.id, "external_user_id": r.external_user_id}), 201

@api.get("/respondents")
def list_respondents():
    rs = Respondent.query.order_by(Respondent.id.asc()).limit(200).all()
    return jsonify([{"id": r.id, "external_user_id": r.external_user_id} for r in rs])

# ------- Response Sessions (API) -------
@api.post("/sessions")
def create_session():
    data = request.get_json(force=True)
    respondent_id = data.get("respondent_id")
    sess = ResponseSession(respondent_id=respondent_id)
    db.session.add(sess)
    db.session.commit()
    return jsonify({"id": sess.id, "respondent_id": sess.respondent_id, "status": "in_progress"}), 201

@api.patch("/sessions/<int:sid>")
def update_session(sid):
    sess = ResponseSession.query.get_or_404(sid)
    data = request.get_json(force=True)
    if data.get("status") == "completed":
        sess.status = "completed"
        sess.completed_at = db.func.now()
    if "meta" in data:
        sess.meta = data["meta"]
    db.session.commit()
    return jsonify({"id": sess.id, "status": sess.status})

@api.get("/sessions")
def list_sessions():
    ss = ResponseSession.query.order_by(ResponseSession.id.asc()).limit(200).all()
    return jsonify([{"id": s.id, "respondent_id": s.respondent_id, "status": s.status} for s in ss])

# ------- Answers (API) -------
@api.post("/answers")
def create_answer():
    data = request.get_json(force=True)
    req = ["response_session_id", "question_id"]
    if any(k not in data for k in req):
        abort(400, "response_session_id and question_id are required")
    a = Answer(
        response_session_id=data["response_session_id"],
        question_id=data["question_id"],
        choice_id=data.get("choice_id"),
        multi_choice_ids=data.get("multi_choice_ids"),
        text_value=data.get("text_value"),
        number_value=data.get("number_value"),
        boolean_value=data.get("boolean_value"),
        meta=data.get("meta") or {},
    )
    db.session.add(a)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        abort(409, "answer for this question already exists in this session")
    return jsonify({"id": a.id}), 201

@api.get("/answers")
def list_answers():
    ans = Answer.query.order_by(Answer.response_session_id.asc(), Answer.question_id.asc()).limit(500).all()
    out = []
    for a in ans:
        out.append({
            "id": a.id,
            "response_session_id": a.response_session_id,
            "question_id": a.question_id,
            "choice_id": a.choice_id,
            "multi_choice_ids": a.multi_choice_ids,
            "text_value": a.text_value,
            "number_value": str(a.number_value) if a.number_value is not None else None,
            "boolean_value": a.boolean_value,
        })
    return jsonify(out)

# ------- Web Admin -------
@web.get("/admin")
def admin_index():
    user_id = current_user.id
    if user_id == 1:
        return render_template("admin_index.html")
    else:
      return "Access denied", 403

@web.get("/admin/categories")
def admin_categories():
    user_id = current_user.id
    if user_id == 1:
        cats = Category.query.order_by(Category.position.asc(), Category.id.asc()).all()
        return render_template("admin_categories.html", categories=cats)
    else:
      return "Access denied", 403

@web.post("/admin/categories")
def admin_create_category():
    name = request.form.get("name")
    if not name:
        flash("Name is required", "error")
        return redirect(url_for("web.admin_categories"))
    cat = Category(name=name, description=request.form.get("description"), position=int(request.form.get("position") or 0))
    db.session.add(cat)
    db.session.commit()
    flash("Category created", "success")
    return redirect(url_for("web.admin_categories"))

@web.get("/admin/questions")
def admin_questions():
    cats = Category.query.order_by(Category.position.asc(), Category.id.asc()).all()
    qs = Question.query.order_by(Question.category_id.asc(), Question.position.asc()).all()
    return render_template("admin_questions.html", categories=cats, questions=qs)

@web.post("/admin/questions")
def admin_create_question():
    category_id = request.form.get("category_id")
    prompt = request.form.get("prompt")
    qtype = request.form.get("type")
    is_required = request.form.get("is_required") == "1"
    position = int(request.form.get("position") or 0)
    meta_raw = request.form.get("meta")
    meta = {}
    if meta_raw:
        try:
            meta = json.loads(meta_raw)
        except Exception:
            flash("Meta must be valid JSON", "error")
            return redirect(url_for("web.admin_questions"))
    if not category_id or not prompt or not qtype:
        flash("Category, prompt and type are required", "error")
        return redirect(url_for("web.admin_questions"))
    q = Question(category_id=int(category_id), prompt=prompt, type=qtype, is_required=is_required, position=position, meta=meta)
    db.session.add(q)
    db.session.commit()
    flash("Question created", "success")
    return redirect(url_for("web.admin_questions"))

@web.get("/admin/choices")
def admin_choices():
    qs = Question.query.order_by(Question.id.desc()).limit(300).all()
    cs = Choice.query.order_by(Choice.question_id.asc(), Choice.position.asc()).all()
    return render_template("admin_choices.html", questions=qs, choices=cs)

@web.post("/admin/choices")
def admin_create_choice():
    qid = request.form.get("question_id")
    label = request.form.get("label")
    value = request.form.get("value")
    position = int(request.form.get("position") or 0)
    meta_raw = request.form.get("meta")
    meta = {}
    if meta_raw:
        try:
            meta = json.loads(meta_raw)
        except Exception:
            flash("Meta must be valid JSON", "error")
            return redirect(url_for("web.admin_choices"))
    if not qid or not label or not value:
        flash("Question, label and value are required", "error")
        return redirect(url_for("web.admin_choices"))
    c = Choice(question_id=int(qid), label=label, value=value, position=position, meta=meta)
    db.session.add(c)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        flash("Value must be unique per question", "error")
        return redirect(url_for("web.admin_choices"))
    flash("Choice created", "success")
    return redirect(url_for("web.admin_choices"))

# ------- Job Roles Admin -------
@web.get("/admin/job_roles")
def admin_job_roles():
    job_roles = JobRole.query.order_by(JobRole.id.desc()).all()
    return render_template("admin_job_roles.html", job_roles=job_roles)

@web.post("/admin/job_roles")
def admin_create_job_role():
    title = request.form.get("title")
    description = request.form.get("description")
    if not title:
        flash("Title is required", "error")
        return redirect(url_for("web.admin_job_roles"))
    job_role = JobRole(title=title, description=description)
    db.session.add(job_role)
    db.session.commit()
    flash("Job Role created", "success")
    return redirect(url_for("web.admin_job_roles"))

@web.post("/admin/job_roles/<int:id>/delete")
def admin_delete_job_role(id):
    job_role = JobRole.query.get_or_404(id)
    db.session.delete(job_role)
    db.session.commit()
    flash("Job Role deleted", "success")
    return redirect(url_for("web.admin_job_roles"))

# ------- Courses Admin -------
@web.get("/admin/courses")
def admin_courses():
    job_roles = JobRole.query.order_by(JobRole.title.asc()).all()
    users = User.query.order_by(User.email.asc()).all()
    courses = Course.query.order_by(Course.id.desc()).all()
    return render_template("admin_courses.html", job_roles=job_roles, users=users, courses=courses)

@web.post("/admin/courses")
def admin_create_course():
    title = request.form.get("title")
    course_title = request.form.get("course_title")
    description = request.form.get("description")
    location = request.form.get("location")
    job_roles_id = request.form.get("job_roles_id")
    timeline = request.form.get("timeline")
    start_date = request.form.get("start_date")
    end_date = request.form.get("end_date")
    
    # New fields
    platform = request.form.get("platform")
    skills_raw = request.form.get("skills")
    rating = request.form.get("rating")
    reviewcount = request.form.get("reviewcount")
    level = request.form.get("level")
    duration = request.form.get("duration")
    certificatetype = request.form.get("certificatetype")
    crediteligibility = request.form.get("crediteligibility") == "1"
    user_id = request.form.get("user_id")
    
    if not title or not job_roles_id:
        flash("Title and Job Role are required", "error")
        return redirect(url_for("web.admin_courses"))
    
    # Parse skills JSON
    skills = []
    if skills_raw:
        try:
            skills = json.loads(skills_raw)
            if not isinstance(skills, list):
                skills = []
        except:
            # If not valid JSON, try to parse as comma-separated string
            skills = [s.strip() for s in skills_raw.split(",") if s.strip()]
    
    course = Course(
        title=title,
        course_title=course_title,
        description=description,
        location=location,
        job_roles_id=int(job_roles_id),
        timeline=timeline,
        start_date=datetime.strptime(start_date, "%Y-%m-%d").date() if start_date else None,
        end_date=datetime.strptime(end_date, "%Y-%m-%d").date() if end_date else None,
        platform=platform,
        skills=skills,
        rating=float(rating) if rating else None,
        reviewcount=int(reviewcount) if reviewcount else None,
        level=level,
        duration=duration,
        certificatetype=certificatetype,
        crediteligibility=crediteligibility,
        user_id=int(user_id) if user_id else None
    )
    db.session.add(course)
    db.session.commit()
    flash("Course created", "success")
    return redirect(url_for("web.admin_courses"))

@web.post("/admin/courses/<int:id>/delete")
def admin_delete_course(id):
    course = Course.query.get_or_404(id)
    db.session.delete(course)
    db.session.commit()
    flash("Course deleted", "success")
    return redirect(url_for("web.admin_courses"))

# ------- Technical Questions Admin -------
@web.get("/admin/technical_questions")
def admin_technical_questions():
    categories = Category.query.order_by(Category.position.asc(), Category.id.asc()).all()
    job_roles = JobRole.query.order_by(JobRole.title.asc()).all()
    technical_questions = TechnicalQuestion.query.order_by(TechnicalQuestion.category_id.asc(), TechnicalQuestion.position.asc()).all()
    return render_template("admin_technical_questions.html", categories=categories, job_roles=job_roles, technical_questions=technical_questions)

@web.post("/admin/technical_questions")
def admin_create_technical_question():
    category_id = request.form.get("category_id")
    job_roles_id = request.form.get("job_roles_id")
    prompt = request.form.get("prompt")
    qtype = request.form.get("type")
    is_required = request.form.get("is_required") == "1"
    position = int(request.form.get("position") or 0)
    meta_raw = request.form.get("meta")
    meta = {}
    if meta_raw:
        try:
            meta = json.loads(meta_raw)
        except Exception:
            flash("Meta must be valid JSON", "error")
            return redirect(url_for("web.admin_technical_questions"))
    if not category_id or not prompt or not qtype:
        flash("Category, prompt and type are required", "error")
        return redirect(url_for("web.admin_technical_questions"))
    
    tq = TechnicalQuestion(
        category_id=int(category_id),
        job_roles_id=int(job_roles_id) if job_roles_id else None,
        prompt=prompt,
        type=qtype,
        is_required=is_required,
        position=position,
        meta=meta
    )
    db.session.add(tq)
    db.session.commit()
    flash("Technical Question created", "success")
    return redirect(url_for("web.admin_technical_questions"))

@web.post("/admin/technical_questions/<int:id>/delete")
def admin_delete_technical_question(id):
    tq = TechnicalQuestion.query.get_or_404(id)
    db.session.delete(tq)
    db.session.commit()
    flash("Technical Question deleted", "success")
    return redirect(url_for("web.admin_technical_questions"))

# ------- Live Jobs Admin -------
@web.get("/admin/live_jobs")
def admin_live_jobs():
    job_roles = JobRole.query.order_by(JobRole.title.asc()).all()
    live_jobs = LiveJob.query.order_by(LiveJob.id.desc()).all()
    return render_template("admin_live_jobs.html", job_roles=job_roles, live_jobs=live_jobs)

@web.post("/admin/live_jobs")
def admin_create_live_job():
    title = request.form.get("title")
    location = request.form.get("location")
    description = request.form.get("description")
    salary = request.form.get("salary")
    job_roles_id = request.form.get("job_roles_id")
    start_date = request.form.get("start_date")
    
    if not title or not job_roles_id:
        flash("Title and Job Role are required", "error")
        return redirect(url_for("web.admin_live_jobs"))
    
    live_job = LiveJob(
        title=title,
        location=location,
        description=description,
        salary=salary,
        job_roles_id=int(job_roles_id),
        start_date=datetime.strptime(start_date, "%Y-%m-%d").date() if start_date else None
    )
    db.session.add(live_job)
    db.session.commit()
    flash("Live Job created", "success")
    return redirect(url_for("web.admin_live_jobs"))

@web.post("/admin/live_jobs/<int:id>/delete")
def admin_delete_live_job(id):
    live_job = LiveJob.query.get_or_404(id)
    db.session.delete(live_job)
    db.session.commit()
    flash("Live Job deleted", "success")
    return redirect(url_for("web.admin_live_jobs"))

# ------- Technical Choices Admin -------
@web.get("/admin/technical_choices")
def admin_technical_choices():
    technical_questions = TechnicalQuestion.query.order_by(TechnicalQuestion.id.desc()).limit(300).all()
    technical_choices = TechnicalChoice.query.order_by(TechnicalChoice.question_id.asc(), TechnicalChoice.position.asc()).all()
    return render_template("admin_technical_choices.html", technical_questions=technical_questions, technical_choices=technical_choices)

@web.post("/admin/technical_choices")
def admin_create_technical_choice():
    qid = request.form.get("question_id")
    label = request.form.get("label")
    value = request.form.get("value")
    position = int(request.form.get("position") or 0)
    meta_raw = request.form.get("meta")
    meta = {}
    if meta_raw:
        try:
            meta = json.loads(meta_raw)
        except Exception:
            flash("Meta must be valid JSON", "error")
            return redirect(url_for("web.admin_technical_choices"))
    if not qid or not label or not value:
        flash("Question, label and value are required", "error")
        return redirect(url_for("web.admin_technical_choices"))
    tc = TechnicalChoice(question_id=int(qid), label=label, value=value, position=position, meta=meta)
    db.session.add(tc)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        flash("Value must be unique per question", "error")
        return redirect(url_for("web.admin_technical_choices"))
    flash("Technical Choice created", "success")
    return redirect(url_for("web.admin_technical_choices"))

@web.post("/admin/technical_choices/<int:id>/delete")
def admin_delete_technical_choice(id):
    tc = TechnicalChoice.query.get_or_404(id)
    db.session.delete(tc)
    db.session.commit()
    flash("Technical Choice deleted", "success")
    return redirect(url_for("web.admin_technical_choices"))
# --- 3. Step 1: Persona Builder (Refined for User JSON Structure) ---
def build_user_persona(user_profile_json: Dict[str, Any]) -> Dict[str, str]:
    """
    Extracts and cleans all relevant inputs from the nested user_profile JSON 
    into a simple dictionary, and identifies the Primary_Interest_Field for focus.
    """
    
    # Safely access the nested 'responses' dictionary
    responses = user_profile_json.get("user_profile", {}).get("responses", {})
    DEFAULT_ANSWER = "unknown or not provided" # Neutral default constant

    def safe_extract(key: str, default: str = DEFAULT_ANSWER) -> str:
        """Safely extracts the 'answer' from the nested response, cleaning up extra text."""
        # Access the dictionary responses[key]['answer']
        answer = responses.get(key, {}).get("answer", default)
        
        # Remove parenthetical descriptions and convert to lowercase for clean prompting
        return answer.split('(')[0].strip().lower()

    # Explicitly retrieve all 10 answers (Q1 to Q10) from the dynamic input
    situation = safe_extract("Q1_current_status")
    familiarity = safe_extract("Q2_tech_familiarity")
    tech_experience = safe_extract("Q3_tech_experience")
    
    # Q4 MUST be present and valid, based on the user's guarantee.
    interest_area = safe_extract("Q4_interest_area") 
    
    motivation = safe_extract("Q5_motivation")
    skill_level = safe_extract("Q6_skill_level")
    project_experience = safe_extract("Q7_project_experience")
    learning_preference = safe_extract("Q8_learning_preference")
    time_commitment = safe_extract("Q9_time_commitment")
    goal = safe_extract("Q10_goal")

    # Map raw user interest string to the 6 fixed categories (Code & Name)
    interest_map = {
        # System constants defining the mapping
        "building and coding software or apps": "A: Logical & Structured Thinking",
        "working with data and insights": "B: Data & Analytical Insight",
        "designing visuals or user experiences": "C: Creative & User-Centricity",
        "managing systems or ensuring cybersecurity": "D: Systemic & Risk Management",
        "coordinating teams or managing projects": "E: Communication & Stakeholder",
        "creating content or writing documentation": "F: Content & Language Fluency"
    }

    # --- VALIDATION: Ensure Q4 is valid and mapped ---
    if interest_area == DEFAULT_ANSWER:
        # This occurs if Q4_interest_area is completely missing from the input JSON
        raise ValueError("Q4_interest_area is missing from input, violating frontend data guarantee.")

    # Determine the primary category for the Focused Depth Assessment
    primary_category = interest_map.get(interest_area)
    
    if primary_category is None:
        # This occurs if the Q4 answer exists but doesn't match a recognized category key
        raise ValueError(f"Q4_interest_area answer '{interest_area}' is not a recognized mapping to an A-F category. Please check frontend mapping keys.")
    # --- END VALIDATION ---
    
    # Consolidate relevant data for the LLM prompt
    persona_data = {
        "Situation": situation,
        "Familiarity": familiarity,
        "Skill_Level": skill_level,
        "Time": time_commitment,
        "Goal": goal,
        "Primary_Interest_Field": primary_category,
        "Raw_Interest": interest_area
    }
    
    return persona_data

# --- 4. Step 2: LLM Dynamic Question Generator (with Schema) ---
def generate_dynamic_questions(persona_data: Dict[str, str], num_questions=6) -> Dict[str, Any]:
    """Generates dynamic questions using GPT-4o-mini with Pydantic schema."""
    
    # 4.1 Define the primary focus and competencies
    primary_focus = persona_data["Primary_Interest_Field"]
    
    # The categories must be included in the prompt for the LLM to choose from
    competency_map = {
        "A": "Logical & Structured Thinking (SW/Dev)",
        "B": "Data & Analytical Insight (Data/ML)",
        "C": "Creative & User-Centricity (Design/UX)",
        "D": "Systemic & Risk Management (Infra/Security)",
        "E": "Communication & Stakeholder (Management/PM)",
        "F": "Content & Language Fluency (Technical Writing/Digital)"
    }

    # 4.2 Define the System Prompt
    system_prompt = f"""
    You are an expert behavioral analyst and career coach. 
    You generate EXACTLY 6 close-ended, non-technical behavioral questions — one for each competency A-F.
    Your output MUST be a STRICT JSON object following the schema you were given:
    - DynamicAssessment
    - DynamicQuestion
    - QuestionOptions
    Do NOT include markdown, explanations, or commentary.
    Only produce raw JSON.
    
    =====================
    CRITICAL INSTRUCTIONS
    =====================
    1. Each question MUST be a realistic behavioral scenario describing an everyday situation 
    (e.g., organizing tasks, solving problems, making decisions, communicating).
    
    2. Each answer option A-D MUST be a short *behavioral micro-profile*:  
    • 1-2 natural-language sentences  
    • Describing HOW the user behaves  
    • Not generic labels like “Agree/Disagree”  
    • NOT abstract traits  
    • NOT one-word adjectives  
    • NOT generic Likert scale labels (Strongly Agree, Agree, etc.)
    
    3. The 4 answer options MUST reflect descending alignment with the competency:
    A = strong alignment  
    B = moderate-high alignment  
    C = moderate-low alignment  
    D = weak alignment
    
    4. Each option MUST function as meaningful semantic text for TF-IDF.  
    Options MUST describe actual actions, habits, or preferences.
    
    Example of GOOD option:
    “I usually break tasks into steps and track my progress with notes or digital tools.”
    
    Example of BAD option (NOT allowed):  
    “Agree”  
    “Strongly agree”  
    “Often”  
    “Sometimes I plan things”  
    “I am organized”
    
    5. Each question MUST correspond to exactly one competency:
    A - Logical & Structured Thinking  
    B - Data & Analytical Insight  
    C - Creative & User-Centricity  
    D - Systemic & Risk Management  
    E - Communication & Stakeholder  
    F - Content & Language Fluency
    
    6. The question for the user's declared primary interest ('{persona_data['Raw_Interest']}') must be more detailed and more probing than the others.
    
    - exactly ONE question  
    - significantly more detailed  
    - based on a realistic scenario in that interest area  
    - deeper, richer, and more specific than the other 5  
    - containing more nuance, context, and behavioral depth  
    - measuring HOW the user behaves in situations relevant to that field

    RULES FOR THIS ONE DEEP QUESTION:
    - The scenario MUST be meaningfully tied to the field (Data, Software, Design, Infra, PM, Content) WITHOUT using technical jargon.
    - The answer options MUST include field-relevant behavioral differences, NOT technical differences.
    - Make sure this question feels personalized to the user's persona AND their chosen field.
    - This deep question MUST appear FIRST in the final list of 6.
    - The competency of this deep question MUST match the user's primary mapped competency (A-F).

    7. Absolutely NO technical references (e.g., Python, SQL, UX design tools).
    
    8. Your final JSON MUST pass the provided Pydantic validation.
    Produce ONLY valid JSON.
    """

    system_prompt += """
    =====================
    STRICT JSON FORMAT
    =====================
    Your final output MUST be a valid JSON object matching this EXACT structure:
    {
        "user_context_summary": "string",
        "questions": [
            {
                "competency": "A|B|C|D|E|F",
                "competency_name": "string",
                "question_text": "string",
                "options": {
                    "A": "string",
                    "B": "string",
                    "C": "string",
                    "D": "string"
                    }
            }
                    ]
    }
    
    REMINDERS:
    - "user_context_summary" MUST always be present.
    - "user_context_summary" MUST be a 3-5 word micro-persona phrase.
    It must combine the user's experience level, motivation or mindset, 
    and primary interest field. It MUST feel descriptive and human, not generic.
    
    Examples of GOOD summaries:
    • “enthusiastic beginner exploring UX”
    • “motivated career shifter into data”
    • “detail-driven learner pursuing software”
    • “creative thinker exploring content tech”
    
    Examples NOT allowed:
    • “beginner”
    • “tech learner”
    • “student interested in design”
    • “job seeker”
    
    - Output MUST NOT contain markdown.
    - Output MUST NOT include commentary.
    - Produce ONLY valid JSON.

    Produce ONLY that JSON object as your final output.
    """

    # 4.3 Define the User Prompt
    user_prompt = f"""
    USER FULL PERSONA:
    - Current Status: {persona_data['Situation']}
    - Tech Familiarity: {persona_data['Familiarity']}
    - Skill Level: {persona_data['Skill_Level']}
    - Weekly Time Commitment: {persona_data['Time']}
    - Main Goal: {persona_data['Goal']}
    - Primary Interest Area: {persona_data['Raw_Interest']}
    - Primary Competency Focus: {persona_data['Primary_Interest_Field']}

    IMPORTANT REQUIREMENTS FOR GENERATION:
    - The VERY FIRST question must be the deep, personalized question aligned to the user's primary interest area.
    - The remaining 5 questions must be general behavioral assessments covering the remaining 5 competencies.
    - Do NOT generate 2 deep questions. Only ONE deep question is allowed.
    - Do NOT generate a deep question for any other competency.
 
    Generate the 6 required questions now.
    """
    
    # 4.4 Make the API Call
    try:
        response = client.responses.create(
            model="gpt-4o-mini",
            temperature=0.7, 
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )
        
        raw_content = response.output_text
        print("RAW MODEL OUTPUT:\n", raw_content)

        # 4.5 Runtime Schema Validation (Pydantic Model Validation)
        validated_data = DynamicAssessment.model_validate_json(raw_content)
        return validated_data.model_dump()
        
    except ValidationError as e:
        # Pydantic validation failed (LLM returned malformed JSON or invalid data types)
        print(f"Validation Error: {e.errors()}")
        return {"error": "LLM failed schema validation. Retrying or falling back recommended.", "detail": str(e.errors())}
    except Exception as e:
        # API errors, network issues, etc.
        return {"error": f"API or processing error: {e}"}


@web.route("/generate_dynamic_questions", methods=["GET","POST"])
def api_generate_dynamic_questions():
    if not api_key:
        return jsonify({"error": "OpenAI API Key not configured."}), 500
        
    try:
        user_base_json = request.get_json()
        if not user_base_json:
            return jsonify({"error": "Missing or invalid JSON payload"}), 400

        # Build persona data based on user's provided structure
        persona_data = build_user_persona(user_base_json)
        
        # Generate questions
        output = generate_dynamic_questions(persona_data)
        
        # Check for errors returned by the generator function itself
        if "error" in output:
            # Return LLM/Validation errors as 500
            return jsonify(output), 500

        # The output is already a validated dictionary
        return jsonify(output), 200

    except Exception as e:
        # Catch unexpected errors during request processing
        return jsonify({"error": str(e)}), 500
 
# Generate Tech Roles
@web.route("/generate_tech_roles", methods=["GET","POST"])
def recommend_roles():
    """
    Input:
    {
        "base_persona_data": {...},
        "dynamic_questions_data": {...}
    }
    """

    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON input"}), 400

        base_data = data.get("base_persona_data")
        dynamic_data = data.get("dynamic_questions_data")

        if not base_data or not dynamic_data:
            return jsonify({
                "error": "Missing 'base_persona_data' or 'dynamic_questions_data'."
            }), 400

    except Exception as e:
        return jsonify({"error": f"Failed to parse input JSON: {e}"}), 400

    try:
        # 1) Build the final_payloa
        final_payload = merge_for_model(base_data, dynamic_data)

        # 2) Generate recommendations
        top_roles = recommend(
            final_payload=final_payload,
            roles=ORDERED_ROLES,
            vectorizer=VECTORIZER,
            role_ids=ROLE_IDS,
            role_tfidf_matrix=ROLE_TFIDF_MATRIX
        )

    except Exception as e:
        print("Error while generating recommendations:", e)
        return jsonify({"error": "Internal processing error"}), 500

    return jsonify({
        "status": "success",
        "top_recommendations": top_roles
    }), 200

# Generate Tech Roles
@web.route("/accept_tech_role", methods=["GET","POST"])
def accept_role():
    data = request.get_json()
    user_id = data.get("user_id")
    job_role = data.get("selected_role")
    roles = JobRole.query.filter(JobRole.title.ilike(f"%{job_role}%")).all()
    role_id = roles[0].id
    user = User.query.get(user_id)
    first_name = user.firstname
    user.job_role_id = role_id
    db.session.commit()
    conn = http.client.HTTPConnection("127.0.0.1", 5011)
    payload = json.dumps({
    "top_role": "Software Engineer",
    "top_n": 3
    })
    headers = {
    'Content-Type': 'application/json'
    }
    conn.request("POST", "/recommend-course", payload, headers)
    res = conn.getresponse()
    data = res.read()
    courses_data = json.loads(data)
    for course in courses_data["courses"]:
        course["skills_list"] = list(ast.literal_eval(course["skills"]))
        tc = Course(title=course["course_title"], job_roles_id=role_id, user_id=user_id , duration=course["duration"], level=course["level"], rating=course["rating"], reviewcount=course["reviewcount"], skills=course["skills_list"] )
        db.session.add(tc)
    db.session.commit()
    return render_template("front_courses.html", user_id=user_id, job_role=job_role, timeline=role_id, data=courses_data, first_name=first_name)

# --- 6. Run Flask App ---
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7070, debug=True)
