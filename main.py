from http.client import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Depends
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from pydantic import BaseModel
import os
from dotenv import load_dotenv

load_dotenv()
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# SQLite 데이터베이스 설정
DATABASE_URL = "sqlite:///./guestbook.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# 방문록 테이블 모델 정의
class GuestbookEntry(Base):
    __tablename__ = "guestbook"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    message = Column(String, nullable=False)

Base.metadata.create_all(bind=engine)

# 요청 데이터 모델
class GuestbookEntryCreate(BaseModel):
    name: str
    message: str

# 데이터베이스 세션 의존성
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 관리자 비밀번호 설정 (실제 사용 시 환경변수 활용)
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")


# 방문록 메시지 추가 (POST /entries)
@app.post("/entries")
def create_entry(entry: GuestbookEntryCreate, db: Session = Depends(get_db)):
    new_entry = GuestbookEntry(name=entry.name, message=entry.message)
    db.add(new_entry)
    db.commit()
    db.refresh(new_entry)
    return new_entry

# 방문록 메시지 조회 (GET / entries)
@app.get("/entries")
def read_entries(db: Session = Depends(get_db)):
    return db.query(GuestbookEntry).all()

# 방문록 메시지 삭제 (DELETE /entries/{id}) - 관리자만 가능
@app.delete("/entries/{entry_id}")
def delete_entry(entry_id: int, password: str, db: Session = Depends(get_db)):
    if password != ADMIN_PASSWORD:
        raise HTTPException(status_code=403, detail="권한이 없습니다.")

    entry = db.query(GuestbookEntry).filter(GuestbookEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="메시지를 찾을 수 없습니다.")

    db.delete(entry)
    db.commit()
    return {"message": "삭제되었습니다."}