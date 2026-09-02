from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.simulation import SimulationRequest, SimulationResponse
from app.services.simulation_service import (
    run_simulation,
    get_user_simulations,
    get_simulation_by_id,
    delete_simulation
)

router = APIRouter(
    prefix="/simulations",
    tags=["Simulation Engine"],
)

@router.get("/status")
def simulation_status(current_user: User = Depends(get_current_user)):
    return {"status": "Simulation Engine active", "user_id": current_user.user_id}

@router.post("", response_model=SimulationResponse, status_code=status.HTTP_201_CREATED)
def create_simulation(
    request: SimulationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        return run_simulation(db, current_user.user_id, request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("", response_model=List[SimulationResponse])
def get_simulations(
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return get_user_simulations(db, current_user.user_id, limit)

@router.get("/{sim_id}", response_model=SimulationResponse)
def get_simulation(
    sim_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    sim = get_simulation_by_id(db, sim_id, current_user.user_id)
    if not sim:
        raise HTTPException(status_code=404, detail="Simulation not found")
    return sim

@router.delete("/{sim_id}", status_code=status.HTTP_200_OK)
def delete_simulation_endpoint(
    sim_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    success = delete_simulation(db, sim_id, current_user.user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Simulation not found")
    return {"message": "Simulation deleted"}
