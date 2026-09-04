import os
import time
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.user import User
from app.services.digital_twin_service import get_digital_twin_state
from app.services.ai.context_builder import build_ai_context
from app.services.ai.assistant_service import get_ai_response

def run_tests():
    db: Session = SessionLocal()
    user = db.query(User).first()
    if not user:
        print("No users in DB to test with.")
        return
    
    print(f"Testing with user: {user.email}")
    
    try:
        dt_state = get_digital_twin_state(db, user.user_id)
        ai_context = build_ai_context(dt_state)
    except Exception as e:
        print("Failed to build context:", e)
        return
    
    questions = [
        ("Academic", "What is my predicted exam score?"),
        ("Financial", "What is my current saving?"),
        ("Fitness", "How many workouts did I do?"),
        ("Lifestyle", "How consistent are my habits?"),
        ("Goals", "Are my goals on track?"),
        ("Forecasting", "What is my forecast?"),
        ("Cross-domain", "What should I improve right now?")
    ]
    
    for domain, q in questions:
        print(f"\n--- {domain} ---")
        print(f"Q: {q}")
        start = time.time()
        try:
            res = get_ai_response(message=q, ai_context=ai_context, conversation_history=[])
            print(f"A: {res}")
        except Exception as e:
            print(f"Error: {e}")
        print(f"Time: {time.time() - start:.2f}s")
        
    db.close()

if __name__ == "__main__":
    run_tests()
