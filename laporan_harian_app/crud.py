from sqlalchemy.orm import Session
from . import models, schemas
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# --- CRUD untuk User ---
def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = models.User(username=user.username, hashed_password=hashed_password, role=user.role, division_id=user.division_id)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# --- CRUD untuk Division ---
def get_division(db: Session, division_id: int):
    return db.query(models.Division).filter(models.Division.id == division_id).first()

def get_division_by_name(db: Session, name: str):
    return db.query(models.Division).filter(models.Division.name == name).first()

def get_divisions(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Division).offset(skip).limit(limit).all()

def create_division(db: Session, division: schemas.DivisionCreate):
    db_division = models.Division(name=division.name)
    db.add(db_division)
    db.commit()
    db.refresh(db_division)
    return db_division

# --- CRUD untuk Report ---
def create_user_report(db: Session, report: schemas.ReportCreate, user_id: int):
    db_report = models.Report(**report.dict(), owner_id=user_id)
    db.add(db_report)
    db.commit()
    db.refresh(db_report)
    return db_report

def get_reports(db: Session, user_id: int = None, skip: int = 0, limit: int = 100):
    query = db.query(models.Report)
    if user_id:
        query = query.filter(models.Report.owner_id == user_id)
    return query.offset(skip).limit(limit).all()
