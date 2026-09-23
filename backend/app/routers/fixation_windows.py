from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models.dye_lot import DyeLot
from app.models.fabric_weight import FabricWeightRecord
from app.models.fixation_window import FixationWindow
from app.models.user import User
from app.models.vat import Vat
from app.schemas.fixation_window import (
    FixationWindowCreate,
    FixationWindowFinish,
    FixationWindowOut,
)
from app.services.fixation import get_active_window, as_utc

router = APIRouter(prefix="/api/fixation-windows", tags=["fixation-windows"])


@router.get("", response_model=List[FixationWindowOut])
def list_windows(
    dye_lot_id: Optional[int] = Query(None, alias="dyeLotId"),
    active_only: bool = Query(False, alias="activeOnly"),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = db.query(FixationWindow)
    if dye_lot_id is not None:
        q = q.filter(FixationWindow.dye_lot_id == dye_lot_id)
    if active_only:
        q = q.filter(FixationWindow.actual_end_at.is_(None))
    return q.order_by(FixationWindow.id.desc()).all()


@router.post("", response_model=FixationWindowOut, status_code=status.HTTP_201_CREATED)
def create_window(
    payload: FixationWindowCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    lot = db.query(DyeLot).filter(DyeLot.id == payload.dye_lot_id).first()
    if not lot:
        raise HTTPException(status_code=400, detail="染程不存在")

    vat = db.query(Vat).filter(Vat.id == lot.vat_id).first()
    if vat and vat.status == "drain":
        raise HTTPException(status_code=409, detail="染缸已排液，禁止新开固色静置")

    # 与色牢度拦截共用同一"进行中"查询
    if get_active_window(db, payload.dye_lot_id):
        raise HTTPException(status_code=409, detail="该染程已有进行中的固色静置，未结束前不得重复开静置")

    item = FixationWindow(
        dye_lot_id=payload.dye_lot_id,
        start_at=payload.start_at,
        planned_end_at=payload.planned_end_at,
        duty_officer=payload.duty_officer,
    )
    db.add(item)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="该染程已有进行中的固色静置，未结束前不得重复开静置")
    db.refresh(item)
    return item


@router.get("/{window_id}", response_model=FixationWindowOut)
def get_window(
    window_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    item = db.query(FixationWindow).filter(FixationWindow.id == window_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="固色静置不存在")
    return item


@router.post("/{window_id}/finish", response_model=FixationWindowOut)
def finish_window(
    window_id: int,
    payload: FixationWindowFinish,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """结束静置：写实际结束（不得早于开始），同事务要求至少一条布重记录可对账。"""
    item = db.query(FixationWindow).filter(FixationWindow.id == window_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="固色静置不存在")
    if item.actual_end_at is not None:
        raise HTTPException(status_code=409, detail="该固色静置已结束")
    if as_utc(payload.actual_end_at) < as_utc(item.start_at):
        raise HTTPException(status_code=400, detail="实际结束时刻不得早于开始时刻")

    weight_count = (
        db.query(FabricWeightRecord)
        .filter(FabricWeightRecord.dye_lot_id == item.dye_lot_id)
        .count()
    )
    if weight_count < 1:
        raise HTTPException(
            status_code=400,
            detail="该染程尚无布重（千克）记录可对账，无法结束固色静置",
        )

    item.actual_end_at = payload.actual_end_at
    db.commit()
    db.refresh(item)
    return item
