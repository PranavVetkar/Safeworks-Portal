from fastapi import APIRouter, Depends, HTTPException, status
import sqlite3
from typing import List
from pydantic import BaseModel
from db import get_db

router = APIRouter(prefix="/hc", tags=["Hiring Client"])

class RequirementCreate(BaseModel):
    hc_id: int
    name: str
    description: str
    workers_required: int
    start_date: str

class RequirementResponse(BaseModel):
    id: int
    hc_id: int
    name: str
    description: str
    workers_required: int
    start_date: str
    ai_validated_description: str | None = None

@router.post("/requirements/", response_model=RequirementResponse)
def create_requirement(req: RequirementCreate, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute('''
        INSERT INTO requirements (hc_id, name, description, workers_required, start_date)
        VALUES (?, ?, ?, ?, ?)
    ''', (req.hc_id, req.name, req.description, req.workers_required, req.start_date))
    db.commit()
    req_id = cursor.lastrowid
    
    # Fetch the inserted requirement
    cursor.execute("SELECT * FROM requirements WHERE id = ?", (req_id,))
    row = cursor.fetchone()
    return dict(row)

@router.get("/requirements/{hc_id}", response_model=List[RequirementResponse])
def list_requirements(hc_id: int, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM requirements WHERE hc_id = ?", (hc_id,))
    rows = cursor.fetchall()
    return [dict(row) for row in rows]

@router.get("/requirements/{req_id}/shortlisted")
def get_shortlisted_for_hc(req_id: int, db: sqlite3.Connection = Depends(get_db)):
    """Returns shortlisted contractor submission data for a given requirement (for HC view)."""
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
