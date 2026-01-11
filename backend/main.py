from dotenv import load_dotenv
import os

load_dotenv()

from fastapi import FastAPI, HTTPException, Depends, Request
from pydantic import BaseModel, HttpUrl
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from services.scraper import WikiScraper
from services.quiz_generator import generate_quiz

from app.core.database import SessionLocal, engine, Base
from app.models.article import WikipediaArticle
from app.models.quiz import Quiz
from app.models.question import Question

from routes_history import router as history_router


GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY is missing in environment variables")


app = FastAPI(title="AI Wiki Quiz Generator")


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",                      
        "https://ai-wiki-quiz-generator-mu.vercel.app"  
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.options("/{path:path}")
async def preflight_handler(path: str, request: Request):
    return JSONResponse(status_code=200, content={})


Base.metadata.create_all(bind=engine)


class WikiRequest(BaseModel):
    url: HttpUrl
    num_questions: int = 5



def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



@app.get("/")
def read_root():
    return {"status": "Scraping API is running"}


@app.post("/generate-quiz")
def generate_quiz_api(request: WikiRequest, db: Session = Depends(get_db)):
    try:
       
        scraper = WikiScraper(str(request.url))
        article_data = scraper.parse()

       
        article = db.query(WikipediaArticle).filter_by(url=str(request.url)).first()
        if not article:
            article = WikipediaArticle(
                url=str(request.url),
                title=article_data["title"],
                summary=article_data["summary"]
            )
            db.add(article)
            db.commit()
            db.refresh(article)

       
        quiz_data = generate_quiz(article_data, request.num_questions)

        
        quiz = Quiz(
            article_id=article.id,
            quiz_title=quiz_data["quiz_title"]
        )
        db.add(quiz)
        db.commit()
        db.refresh(quiz)

        
        for q in quiz_data["questions"]:
            question = Question(
                quiz_id=quiz.id,
                question=q["question"],
                options=q["options"],
                correct_answer=q["correct_answer"],
                difficulty=q["difficulty"],
                explanation=q["explanation"],
                related_topics=q["related_topics"]
            )
            db.add(question)

        db.commit()

        return {
            "quiz_id": quiz.id,
            **quiz_data
        }

    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/quiz/{quiz_id}")
def get_quiz(quiz_id: int, db: Session = Depends(get_db)):
    quiz = db.query(Quiz).filter_by(id=quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    questions = db.query(Question).filter_by(quiz_id=quiz_id).all()

    return {
        "quiz_id": quiz.id,
        "quiz_title": quiz.quiz_title,
        "questions": [
            {
                "id": q.id,
                "question": q.question,
                "options": q.options,
                "correct_answer": q.correct_answer,
                "difficulty": q.difficulty,
                "explanation": q.explanation,
                "related_topics": q.related_topics
            }
            for q in questions
        ]
    }



app.include_router(history_router)
