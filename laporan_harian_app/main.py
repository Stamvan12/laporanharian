import os
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Depends, status
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordRequestForm
from pathlib import Path
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, time
import shutil
import cloudinary
import cloudinary.uploader

from . import database, models, schemas, crud, auth # Import crud dan auth

app = FastAPI()

# Dapatkan path absolut dari direktori tempat main.py berada
BASE_DIR = Path(__file__).parent

# Direktori untuk menyimpan file statis (HTML, CSS, JS)
STATIC_DIR = BASE_DIR / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Direktori untuk menyimpan data database (SQLite lokal)
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# Konfigurasi Cloudinary
cloudinary.config(
    cloud_name=os.environ.get("CLOUDINARY_CLOUD_NAME"),
    api_key=os.environ.get("CLOUDINARY_API_KEY"),
    api_secret=os.environ.get("CLOUDINARY_API_SECRET"),
    secure=True
)

# Dependency untuk mendapatkan sesi database
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.on_event("startup")
async def startup_event():
    # Pastikan database.SQLALCHEMY_DATABASE_URL menggunakan DATA_DIR jika lokal
    if "DATABASE_URL" not in os.environ:
        database.SQLALCHEMY_DATABASE_URL = f"sqlite:///{DATA_DIR / 'sql_app.db'}"
        database.engine = database.create_engine(
            database.SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
        )
        database.SessionLocal = database.sessionmaker(autocommit=False, autoflush=False, bind=database.engine)

    # Buat tabel database saat aplikasi dimulai
    database.create_db_tables()
    db = database.SessionLocal()

    # Tambahkan data awal jika database kosong (contoh divisi)
    if db.query(models.Division).count() == 0:
        crud.create_division(db, schemas.DivisionCreate(name="HRD"))
        crud.create_division(db, schemas.DivisionCreate(name="FINANCE"))
        crud.create_division(db, schemas.DivisionCreate(name="SPV"))
        crud.create_division(db, schemas.DivisionCreate(name="KEPALA TOKO DAYODARA"))
        crud.create_division(db, schemas.DivisionCreate(name="KEPALA TOKO TAWAELI"))
        crud.create_division(db, schemas.DivisionCreate(name="FL"))
        crud.create_division(db, schemas.DivisionCreate(name="OPERASIONAL CEMILAN"))
        crud.create_division(db, schemas.DivisionCreate(name="OPERASIONAL KRIBANGS"))
        print("Divisi awal ditambahkan.")

    # Tambahkan contoh pengguna jika belum ada
    if crud.get_user_by_username(db, username="employee1") is None:
        crud.create_user(db, schemas.UserCreate(username="employee1", password="password", role="employee", division_id=db.query(models.Division).filter_by(name="OPERASIONAL KRIBANGS").first().id))
        print("Contoh employee1 ditambahkan.")

    # Tambahkan pengguna SPV tetap jika belum ada
    if crud.get_user_by_username(db, username="spvkribangs96") is None:
        # PENTING: Kredensial hardcoded ini TIDAK AMAN untuk produksi.
        # Gunakan variabel lingkungan atau sistem manajemen rahasia.
        spv_division = db.query(models.Division).filter_by(name="SPV").first()
        if spv_division:
            crud.create_user(db, schemas.UserCreate(username="spvkribangs96", password="kribangs96", role="spv", division_id=spv_division.id))
            print("Pengguna SPV tetap 'spvkribangs96' ditambahkan.")
        else:
            print("Peringatan: Divisi SPV tidak ditemukan, pengguna SPV tetap tidak dapat ditambahkan.")
    db.close()

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """
    Menyajikan halaman HTML utama aplikasi.
    """
    with open(STATIC_DIR / "index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

# Endpoint ini tidak lagi diperlukan karena foto diunggah ke Cloudinary
# @app.get("/uploads/{filename})
# async def get_uploaded_file(filename: str):
#     """
#     Menyajikan file yang diunggah (foto).
#     """
#     file_path = UPLOAD_DIR / filename
#     if not file_path.is_file():
#         raise HTTPException(status_code=404, detail="File not found")
#     return FileResponse(file_path)

@app.post("/token", response_model=schemas.Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    user = crud.get_user_by_username(db, username=form_data.username)
    if not user or not crud.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.username, "role": user.role},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer", "role": user.role, "username": user.username}

@app.post("/register", response_model=schemas.User)
async def register_user(user: schemas.UserCreate, db: Session = Depends(database.get_db)):
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    # Pastikan division_id valid
    division = crud.get_division(db, user.division_id)
    if not division:
        raise HTTPException(status_code=400, detail="Invalid division ID")
    # user.role akan selalu 'employee' dari frontend
    return crud.create_user(db=db, user=user)

@app.get("/users/me", response_model=schemas.User)
async def read_users_me(current_user: models.User = Depends(auth.get_current_active_user)):
    return current_user

@app.get("/users/{user_id}", response_model=schemas.User)
async def read_user_by_id(user_id: int, db: Session = Depends(database.get_db)):
    user = crud.get_user(db, user_id=user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.get("/divisions", response_model=list[schemas.Division])
async def get_divisions(db: Session = Depends(database.get_db)):
    """
    Mengambil daftar semua divisi.
    """
    divisions = crud.get_divisions(db)
    return divisions

@app.post("/report", status_code=status.HTTP_201_CREATED)
async def create_report(
    report_text: str = Form(...),
    report_photo: UploadFile = File(None),
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_active_user) # Autentikasi di sini
):
    """
    Menerima laporan baru (teks dan opsional foto) dan menyimpannya ke database.
    """
    photo_url = None
    if report_photo and report_photo.filename:
        try:
            # Unggah foto ke Cloudinary
            upload_result = cloudinary.uploader.upload(report_photo.file, folder="laporan_harian")
            photo_url = upload_result.get("secure_url")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Gagal mengunggah foto ke Cloudinary: {e}")

    report_data = schemas.ReportCreate(text=report_text, photo_path=photo_url)
    db_report = crud.create_user_report(db=db, report=report_data, user_id=current_user.id)

    return {"message": "Laporan berhasil disimpan", "report": {"time": db_report.timestamp.strftime("%H:%M:%S"), "text": db_report.text, "photo": db_report.photo_path}}

@app.get("/reports")
async def get_reports(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_active_user) # Autentikasi di sini
):
    """
    Mengambil semua laporan untuk hari ini dari database untuk pengguna yang sedang login.
    """
    today = datetime.now().date()
    reports = db.query(models.Report).filter(
        models.Report.owner_id == current_user.id, # Filter berdasarkan user_id
        models.Report.timestamp >= today,
        models.Report.timestamp < today + timedelta(days=1)
    ).order_by(models.Report.timestamp).all()

    # Format laporan untuk frontend
    formatted_reports = []
    for report in reports:
        formatted_reports.append({
            "time": report.timestamp.strftime("%H:%M:%S"),
            "text": report.text,
            "photo": report.photo_path # photo_path sekarang adalah URL Cloudinary
        })
    return {"reports": formatted_reports}

@app.get("/daily_summary")
async def get_daily_summary(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_active_user) # Autentikasi di sini
):
    """
    Menghasilkan rangkuman laporan harian (teks saja, dengan jam) dari database untuk pengguna yang sedang login.
    """
    today = datetime.now().date()
    reports = db.query(models.Report).filter(
        models.Report.owner_id == current_user.id, # Filter berdasarkan user_id
        models.Report.timestamp >= today,
        models.Report.timestamp < today + timedelta(days=1)
    ).order_by(models.Report.timestamp).all()

    if not reports:
        return {"summary": "Belum ada laporan untuk hari ini."}

    summary_lines = [f"Laporan Harian - {datetime.now().strftime("%Y-%m-%d")}", "=" * 30]
    for i, report in enumerate(reports):
        summary_lines.append(f"{i+1}. [{report.timestamp.strftime("%H:%M:%S")}] {report.text}")

    return {"summary": "\n".join(summary_lines)}

# Endpoint untuk SPV (membutuhkan autentikasi SPV)
@app.get("/spv/all_reports", response_model=list[schemas.Report])
async def get_all_reports(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_spv_user) # Hanya SPV yang bisa akses
):
    """
    Mengambil semua laporan dari semua pengguna (hanya untuk SPV).
    """
    reports = db.query(models.Report).order_by(models.Report.timestamp.desc()).all()
    return reports

@app.get("/spv/users_status")
async def get_users_status(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_spv_user) # Hanya SPV yang bisa akses
):
    """
    Mengambil status pelaporan semua pengguna untuk hari ini (hanya untuk SPV).
    """
    today = datetime.now().date()
    users = db.query(models.User).all()
    divisions = {div.id: div.name for div in db.query(models.Division).all()}

    users_status = []
    CHECKPOINTS = [time(10, 0), time(12, 0), time(15, 0)]

    for user in users:
        user_reports_today = db.query(models.Report).filter(
            models.Report.owner_id == user.id,
            models.Report.timestamp >= today,
            models.Report.timestamp < today + timedelta(days=1)
        ).order_by(models.Report.timestamp).all()

        current_datetime = datetime.now()
        current_date = current_datetime.date()
        current_time = current_datetime.time()

        user_status_text = "Sudah lapor semua checkpoint"
        user_last_report_time_display = "N/A"
        has_any_report_today = False

        if user_reports_today:
            has_any_report_today = True
            user_last_report_time_display = user_reports_today[-1].timestamp.strftime("%H:%M:%S")

        overall_late_status_found = False
        overall_missing_status_found = False
        overall_late_submission_found = False
        first_pending_checkpoint_time = None

        for i, cp_time in enumerate(CHECKPOINTS):
            cp_dt = datetime.combine(current_date, cp_time)
            late_threshold_dt = cp_dt + timedelta(hours=1)
            next_cp_dt = None
            if i + 1 < len(CHECKPOINTS):
                next_cp_dt = datetime.combine(current_date, CHECKPOINTS[i+1])

            # Find the first report submitted within this checkpoint's "period"
            # Period: from cp_dt up to (but not including) next_cp_dt
            report_in_this_period = None
            for report in user_reports_today:
                if report.timestamp >= cp_dt:
                    if next_cp_dt is None or report.timestamp < next_cp_dt:
                        report_in_this_period = report
                        break

            if current_datetime >= late_threshold_dt: # Checkpoint period is past its late threshold
                if report_in_this_period is None:
                    user_status_text = f"Terlambat ({cp_time.strftime("%H:%M")})"
                    overall_late_status_found = True
                    break # Most critical status, no need to check further
                elif report_in_this_period.timestamp > cp_dt + timedelta(minutes=10): # Report submitted late for this period
                    overall_late_submission_found = True
                    if not overall_late_status_found: # Only update if not already critically late
                        user_status_text = "Lapor Terlambat"
            elif current_datetime >= cp_dt: # Checkpoint period is active, but not yet late threshold
                if report_in_this_period is None:
                    overall_missing_status_found = True
                    if not overall_late_status_found and not overall_late_submission_found:
                        user_status_text = f"Belum Lapor ({cp_time.strftime("%H:%M")})"
                elif report_in_this_period.timestamp > cp_dt + timedelta(minutes=10):
                    overall_late_submission_found = True
                    if not overall_late_status_found and not overall_missing_status_found:
                        user_status_text = "Lapor Terlambat"
            else: # Checkpoint is in the future
                if first_pending_checkpoint_time is None:
                    first_pending_checkpoint_time = cp_time

        # Final status determination based on flags
        if overall_late_status_found:
            pass # user_status_text is already set to the critical late status
        elif overall_missing_status_found:
            pass # user_status_text is already set to the first missing checkpoint
        elif overall_late_submission_found:
            user_status_text = "Lapor Terlambat"
        elif not has_any_report_today and current_time > CHECKPOINTS[0]:
            user_status_text = "Belum ada laporan hari ini"
        elif first_pending_checkpoint_time:
            user_status_text = f"Menunggu ({first_pending_checkpoint_time.strftime("%H:%M")})"
        else:
            user_status_text = "Sudah lapor semua checkpoint"

        users_status.append({
            "username": user.username,
            "division": divisions.get(user.division_id, "N/A"),
            "role": user.role,
            "last_report_time": user_last_report_time_display,
            "status": user_status_text
        })
    return users_status