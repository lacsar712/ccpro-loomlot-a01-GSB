from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models.dye_lot import DyeLot
from app.models.fabric_weight import FabricWeight
from app.models.fixation_dwell import FixationDwell
from app.models.user import User
from app.models.vat import Vat
from app.schemas.fixation_dwell import (
    FixationDwellCreate,
    FixationDwellEnd,
    FixationDwellOut,
)

router = APIRouter(prefix="/api/fixation-dwells", tags=["fixation-dwells"])


def _as_aware(dt: datetime) -> datetime:
    """无时区输入按 UTC 处理，避免 aware/naive 比较报错。"""
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=timezone.utc)


@router.get("", response_model=List[FixationDwellOut])
def list_dwells(
    dye_lot_id: Optional[int] = Query(None, alias="dyeLotId"),
    active_only: bool = Query(False, alias="activeOnly"),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = db.query(FixationDwell)
    if dye_lot_id is not None:
        q = q.filter(FixationDwell.dye_lot_id == dye_lot_id)
    if active_only:
        q = q.filter(FixationDwell.actual_end_at.is_(None))
    return q.order_by(FixationDwell.id.desc()).all()


@router.post("", response_model=FixationDwellOut, status_code=status.HTTP_201_CREATED)
def create_dwell(
    payload: FixationDwellCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    lot = db.query(DyeLot).filter(DyeLot.id == payload.dye_lot_id).first()
    if not lot:
        raise HTTPException(status_code=400, detail="染程不存在")

    # 计划结束必须晚于开始
    if _as_aware(payload.planned_end_at) <= _as_aware(payload.started_at):
        raise HTTPException(status_code=400, detail="计划结束时刻必须晚于开始时刻")

    # 排液缸上的染程禁止新开静置
    vat = db.query(Vat).filter(Vat.id == lot.vat_id).first()
    if vat and vat.status == "drain":
        raise HTTPException(status_code=409, detail="染缸已排液，禁止新开固色静置")

    # 同染程同时只允许一条未结束静置（与色牢度拦截共用同一查询）
    conflict = FixationDwell.active_query(db, payload.dye_lot_id).first()
    if conflict:
        raise HTTPException(
            status_code=409,
            detail="该染程已有进行中的固色静置，未结束前不得重复挂静置",
        )

    item = FixationDwell(
        dye_lot_id=payload.dye_lot_id,
        started_at=payload.started_at,
        planned_end_at=payload.planned_end_at,
        actual_end_at=None,
        duty_officer=payload.duty_officer,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.get("/{dwell_id}", response_model=FixationDwellOut)
def get_dwell(
    dwell_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    item = db.query(FixationDwell).filter(FixationDwell.id == dwell_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="固色静置不存在")
    return item


@router.post("/{dwell_id}/end", response_model=FixationDwellOut)
def end_dwell(
    dwell_id: int,
    payload: FixationDwellEnd,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    item = db.query(FixationDwell).filter(FixationDwell.id == dwell_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="固色静置不存在")
    if item.actual_end_at is not None:
        raise HTTPException(status_code=400, detail="该静置已结束")

    # 实际结束不得早于开始
    if _as_aware(payload.actual_end_at) < _as_aware(item.started_at):
        raise HTTPException(status_code=400, detail="实际结束时刻不得早于开始时刻")

    # 同事务对账：该染程至少已有一条布重千克记录
    weight_count = (
        db.query(FabricWeight.id)
        .filter(FabricWeight.dye_lot_id == item.dye_lot_id)
        .count()
    )
    if weight_count < 1:
        raise HTTPException(
            status_code=400,
            detail="该染程尚无布重千克记录可对账，无法结束静置",
        )

    item.actual_end_at = payload.actual_end_at
    db.commit()
    db.refresh(item)
    return item
