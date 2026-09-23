from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models.dye_lot import DyeLot
from app.models.fabric_weight import FabricWeightRecord
from app.models.user import User
from app.schemas.fabric_weight import FabricWeightRecordCreate, FabricWeightRecordOut

router = APIRouter(prefix="/api/fabric-weights", tags=["fabric-weights"])


@router.get("", response_model=List[FabricWeightRecordOut])
def list_weights(
    dye_lot_id: Optional[int] = Query(None, alias="dyeLotId"),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = db.query(FabricWeightRecord)
    if dye_lot_id is not None:
        q = q.filter(FabricWeightRecord.dye_lot_id == dye_lot_id)
    return q.order_by(FabricWeightRecord.id.desc()).all()


@router.post("", response_model=FabricWeightRecordOut, status_code=status.HTTP_201_CREATED)
def create_weight(
    payload: FabricWeightRecordCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    lot = db.query(DyeLot).filter(DyeLot.id == payload.dye_lot_id).first()
    if not lot:
        raise HTTPException(status_code=400, detail="染程不存在")
    item = FabricWeightRecord(
        dye_lot_id=payload.dye_lot_id,
        weighed_at=payload.weighed_at,
        weight_kg=payload.weight_kg,
        recorder_name=payload.recorder_name,
        notes=payload.notes,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item
