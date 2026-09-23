from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models.dye_lot import DyeLot
from app.models.fabric_weight import FabricWeight
from app.models.user import User
from app.schemas.fabric_weight import (
    FabricWeightCreate,
    FabricWeightUpdate,
    FabricWeightOut,
)

router = APIRouter(prefix="/api/fabric-weights", tags=["fabric-weights"])


@router.get("", response_model=List[FabricWeightOut])
def list_weights(
    dye_lot_id: Optional[int] = Query(None, alias="dyeLotId"),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = db.query(FabricWeight)
    if dye_lot_id is not None:
        q = q.filter(FabricWeight.dye_lot_id == dye_lot_id)
    return q.order_by(FabricWeight.id.desc()).all()


@router.post("", response_model=FabricWeightOut, status_code=status.HTTP_201_CREATED)
def create_weight(
    payload: FabricWeightCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    lot = db.query(DyeLot).filter(DyeLot.id == payload.dye_lot_id).first()
    if not lot:
        raise HTTPException(status_code=400, detail="染程不存在")
    item = FabricWeight(
        dye_lot_id=payload.dye_lot_id,
        weighed_at=payload.weighed_at,
        weight_kg=payload.weight_kg,
        recorder_name=payload.recorder_name,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.get("/{weight_id}", response_model=FabricWeightOut)
def get_weight(
    weight_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    item = db.query(FabricWeight).filter(FabricWeight.id == weight_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="布重记录不存在")
    return item


@router.put("/{weight_id}", response_model=FabricWeightOut)
def update_weight(
    weight_id: int,
    payload: FabricWeightUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    item = db.query(FabricWeight).filter(FabricWeight.id == weight_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="布重记录不存在")
    data = payload.model_dump(exclude_unset=True)
    if "dye_lot_id" in data:
        lot = db.query(DyeLot).filter(DyeLot.id == data["dye_lot_id"]).first()
        if not lot:
            raise HTTPException(status_code=400, detail="染程不存在")
    for k, v in data.items():
        setattr(item, k, v)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{weight_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_weight(
    weight_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    item = db.query(FabricWeight).filter(FabricWeight.id == weight_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="布重记录不存在")
    db.delete(item)
    db.commit()
