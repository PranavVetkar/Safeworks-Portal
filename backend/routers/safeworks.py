from fastapi import APIRouter, Depends, HTTPException, status
import sqlite3
from typing import List, Optional
from pydantic import BaseModel
from db import get_db
from services.ai_service import validate_requirement_ai

router = APIRouter(prefix="/safeworks", tags=["Safeworks"])

class RequirementResponse(BaseModel):
    id: int
    hc_id: int
    name: str
    description: str
    workers_required: int
    start_date: str
    ai_validated_description: str | None = None

class ForwardRequest(BaseModel):
    contractor_ids: List[int]

class SubmissionResponse(BaseModel):
    submission_id: int
    contractor_id: int
    contractor_name: str
    worker_ids: str
    readiness_date: str
    workers_committed: Optional[int] = 0
    workers_ready: Optional[int] = 0
    workers_to_onboard: Optional[int] = 0

class ShortlistRequest(BaseModel):
    contractor_ids: List[int]

@router.get("/requirements/")
def list_all_requirements(db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM requirements")
    rows = cursor.fetchall()
    return [dict(row) for row in rows]

@router.post("/requirements/{req_id}/validate", response_model=RequirementResponse)
def validate_requirement(req_id: int, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM requirements WHERE id = ?", (req_id,))
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Requirement not found")
    
    req_dict = dict(row)
    enhanced_desc = validate_requirement_ai(req_dict['description'])
    
    cursor.execute('''
        UPDATE requirements 
        SET ai_validated_description = ? 
        WHERE id = ?
    ''', (enhanced_desc, req_id))
    db.commit()
    
    cursor.execute("SELECT * FROM requirements WHERE id = ?", (req_id,))
    updated_row = cursor.fetchone()
    return dict(updated_row)

@router.post("/requirements/{req_id}/forward")
def forward_requirement(req_id: int, request: ForwardRequest, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    
    # insert each contractor
    for contractor_id in request.contractor_ids:
        try:
            cursor.execute('''
                INSERT INTO requirement_assignments (requirement_id, contractor_id)
                VALUES (?, ?)
            ''', (req_id, contractor_id))
        except sqlite3.IntegrityError:
            pass # ignore duplicates
            
    db.commit()
    return {"message": "Requirement successfully forwarded to selected contractors."}

@router.get("/submissions/{req_id}", response_model=List[SubmissionResponse])
def get_submissions_for_requirement(req_id: int, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute('''
        SELECT s.id as submission_id, s.contractor_id, u.name as contractor_name,
               s.worker_ids, s.readiness_date,
               COALESCE(s.workers_committed, 0) as workers_committed,
               COALESCE(s.workers_ready, 0) as workers_ready,
               COALESCE(s.workers_to_onboard, 0) as workers_to_onboard
        FROM submissions s
        JOIN users u ON s.contractor_id = u.id
        WHERE s.requirement_id = ?
    ''', (req_id,))
    rows = cursor.fetchall()
    return [dict(row) for row in rows]

@router.get("/submissions/{req_id}/workers")
def get_submission_workers(req_id: int, db: sqlite3.Connection = Depends(get_db)):
    """Returns per-contractor lists of their selected workers with details."""
    cursor = db.cursor()
    cursor.execute('''
        SELECT s.contractor_id, u.name as contractor_name, s.worker_ids
        FROM submissions s
        JOIN users u ON s.contractor_id = u.id
        WHERE s.requirement_id = ?
    ''', (req_id,))
    submissions = cursor.fetchall()
    
    result = []
    for sub in submissions:
        contractor_id = sub['contractor_id']
        contractor_name = sub['contractor_name']
        worker_ids_str = sub['worker_ids'] or ''
        worker_ids = [int(w) for w in worker_ids_str.split(',') if w.strip()]
        
        workers = []
        for wid in worker_ids:
            cursor.execute("SELECT * FROM workers WHERE id = ?", (wid,))
            w = cursor.fetchone()
            if w:
                workers.append(dict(w))
        
        result.append({
            'contractor_id': contractor_id,
            'contractor_name': contractor_name,
            'workers': workers
        })
    return result

@router.post("/requirements/{req_id}/shortlist")
def shortlist_contractors(req_id: int, request: ShortlistRequest, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    for contractor_id in request.contractor_ids:
        try:
            cursor.execute('''
                INSERT INTO shortlisted_contractors (requirement_id, contractor_id)
                VALUES (?, ?)
            ''', (req_id, contractor_id))
        except sqlite3.IntegrityError:
            pass
    db.commit()
    return {"message": "Contractors shortlisted successfully"}

@router.get("/requirements/{req_id}/shortlisted")
def get_shortlisted_contractors(req_id: int, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute('''
        SELECT sc.contractor_id, u.name as contractor_name,
               s.worker_ids, s.readiness_date,
               COALESCE(s.workers_committed, 0) as workers_committed,
               COALESCE(s.workers_ready, 0) as workers_ready,
               COALESCE(s.workers_to_onboard, 0) as workers_to_onboard
        FROM shortlisted_contractors sc
        JOIN users u ON sc.contractor_id = u.id
        LEFT JOIN submissions s ON s.contractor_id = sc.contractor_id AND s.requirement_id = sc.requirement_id
        WHERE sc.requirement_id = ?
    ''', (req_id,))
    rows = cursor.fetchall()
    return [dict(row) for row in rows]
