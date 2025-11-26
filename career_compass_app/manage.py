from app import create_app
from app.extensions import db
from app.models import Category, Question, Choice, Respondent, ResponseSession, Answer

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {
        "db": db,
        "Category": Category,
        "Question": Question,
        "Choice": Choice,
        "Respondent": Respondent,
        "ResponseSession": ResponseSession,
        "Answer": Answer,
    }
