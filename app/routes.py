from flask import Blueprint, request, jsonify, abort, render_template, redirect, url_for, flash
from .extensions import db
from .models import Category, Question, Choice, Respondent, ResponseSession, Answer,TechnicalQuestion,TechnicalChoice, JobRole, Course, LiveJob
from sqlalchemy.exc import IntegrityError
from flask_security import auth_required
import json
from datetime import datetime
from flask_login import current_user, login_required


api = Blueprint("api", __name__)
web = Blueprint("web", __name__)

@web.get("/")
@auth_required() 
def health():
    cats = Category.query.order_by(Category.position.asc(), Category.id.asc()).all()
    qs = Question.query.order_by(Question.category_id.asc(), Question.position.asc()).all()
    user_id = current_user.id
    return render_template("front_index.html", categories=cats, questions=qs, user_id=user_id)
    #return {"status": "hello"}

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
    return render_template("admin_index.html")

@web.get("/admin/categories")
def admin_categories():
    cats = Category.query.order_by(Category.position.asc(), Category.id.asc()).all()
    return render_template("admin_categories.html", categories=cats)

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
    courses = Course.query.order_by(Course.id.desc()).all()
    return render_template("admin_courses.html", job_roles=job_roles, courses=courses)

@web.post("/admin/courses")
def admin_create_course():
    title = request.form.get("title")
    description = request.form.get("description")
    location = request.form.get("location")
    job_roles_id = request.form.get("job_roles_id")
    timeline = request.form.get("timeline")
    start_date = request.form.get("start_date")
    end_date = request.form.get("end_date")
    
    if not title or not job_roles_id:
        flash("Title and Job Role are required", "error")
        return redirect(url_for("web.admin_courses"))
    
    course = Course(
        title=title,
        description=description,
        location=location,
        job_roles_id=int(job_roles_id),
        timeline=timeline,
        start_date=datetime.strptime(start_date, "%Y-%m-%d").date() if start_date else None,
        end_date=datetime.strptime(end_date, "%Y-%m-%d").date() if end_date else None
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
