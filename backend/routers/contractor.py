from fastapi import APIRouter, Depends, HTTPException, status
import sqlite3
from typing import List, Dict, Any
from pydantic import BaseModel
from db import get_db
from services.ai_service import check_worker_compatibility

router = APIRouter(prefix="/contractor", tags=["Contractor"])

class WorkerResponse(BaseModel):
    id: int
    contractor_id: int
    name: str
    certifications: str
    years_experience: int

class SubmissionCreate(BaseModel):
    requirement_id: int
    contractor_id: int
    worker_ids: str
    readiness_date: str
    workers_committed: int = 0
    workers_ready: int = 0
    workers_to_onboard: int = 0

@router.get("/requirements/{contractor_id}")
def get_assigned_requirements(contractor_id: int, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute('''
        SELECT r.* FROM requirements r
        JOIN requirement_assignments ra ON r.id = ra.requirement_id
        WHERE ra.contractor_id = ?
    ''', (contractor_id,))
    rows = cursor.fetchall()
    return [dict(row) for row in rows]

@router.get("/workers/{contractor_id}", response_model=List[WorkerResponse])
def get_workers(contractor_id: int, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM workers WHERE contractor_id = ?", (contractor_id,))
    rows = cursor.fetchall()
    return [dict(row) for row in rows]

@router.post("/workers/compatibility")
def check_compatibility(req_id: int, worker_id: int, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM requirements WHERE id = ?", (req_id,))
    req_row = cursor.fetchone()
    
    cursor.execute("SELECT * FROM workers WHERE id = ?", (worker_id,))
    worker_row = cursor.fetchone()

    if not req_row or not worker_row:
        raise HTTPException(status_code=404, detail="Requirement or Worker not found")

    req_details = {
        "name": req_row['name'],
        "description": req_row['description'] or "No description",
        "workers_required": req_row['workers_required'],
        "start_date": req_row['start_date']
    }
    
    worker_details = {
        "name": worker_row['name'],
        "certifications": worker_row['certifications'],
        "years_experience": worker_row['years_experience']
    }

    result = check_worker_compatibility(req_details, worker_details)
    return result

@router.post("/submissions")
def create_submission(submission: SubmissionCreate, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute('''
        INSERT INTO submissions (requirement_id, contractor_id, worker_ids, readiness_date, workers_committed, workers_ready, workers_to_onboard)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (submission.requirement_id, submission.contractor_id, submission.worker_ids, submission.readiness_date,
          submission.workers_committed, submission.workers_ready, submission.workers_to_onboard))
    db.commit()
    sub_id = cursor.lastrowid
    
    cursor.execute("SELECT * FROM submissions WHERE id = ?", (sub_id,))
    row = cursor.fetchone()
    return dict(row)


class CourseAssign(BaseModel):
    course_name: str

@router.get("/workers/{worker_id}/courses")
def get_worker_courses(worker_id: int, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT course_name FROM worker_courses WHERE worker_id = ?", (worker_id,))
    rows = cursor.fetchall()
    return [row['course_name'] for row in rows]

@router.post("/workers/{worker_id}/courses")
def assign_worker_course(worker_id: int, body: CourseAssign, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    # Avoid duplicates
    cursor.execute("SELECT id FROM worker_courses WHERE worker_id = ? AND course_name = ?", (worker_id, body.course_name))
    if not cursor.fetchone():
        cursor.execute("INSERT INTO worker_courses (worker_id, course_name) VALUES (?, ?)", (worker_id, body.course_name))
        db.commit()
    return {"message": "Course assigned"}

@router.delete("/workers/{worker_id}/courses")
def remove_worker_course(worker_id: int, body: CourseAssign, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("DELETE FROM worker_courses WHERE worker_id = ? AND course_name = ?", (worker_id, body.course_name))
    db.commit()
    return {"message": "Course removed"}
