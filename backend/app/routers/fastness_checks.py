from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models.dye_lot import DyeLot
from app.models.fastness_check import FastnessCheck
from app.models.user import User
from app.schemas.fastness_check import FastnessCheckCreate, FastnessCheckUpdate, FastnessCheckOut
from app.services.fixation import get_active_window

router = APIRouter(prefix="/api/fastness-checks", tags=["fastness-checks"])


@router.get("", response_model=List[FastnessCheckOut])
def list_checks(
    dye_lot_id: Optional[int] = Query(None, alias="dyeLotId"),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = db.query(FastnessCheck)
    if dye_lot_id is not None:
        q = q.filter(FastnessCheck.dye_lot_id == dye_lot_id)
    return q.order_by(FastnessCheck.id.desc()).all()


@router.post("", response_model=FastnessCheckOut, status_code=status.HTTP_201_CREATED)
def create_check(
    payload: FastnessCheckCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    lot = db.query(DyeLot).filter(DyeLot.id == payload.dye_lot_id).first()
    if not lot:
        raise HTTPException(status_code=400, detail="染程不存在")
    # 拦截与静置页"是否进行中"判定共用 get_active_window 同一查询
    if get_active_window(db, payload.dye_lot_id):
        raise HTTPException(
            status_code=409,
            detail="该染程固色静置进行中，未满静置窗禁止登记色牢度抽检",
        )
    item = FastnessCheck(
        dye_lot_id=payload.dye_lot_id,
        checked_at=payload.checked_at,
        wash_fastness=payload.wash_fastness,
        rub_fastness=payload.rub_fastness,
        temp_c=payload.temp_c,
        notes=payload.notes,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.get("/{check_id}", response_model=FastnessCheckOut)
def get_check(
    check_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    item = db.query(FastnessCheck).filter(FastnessCheck.id == check_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="色牢度抽检不存在")
    return item


@router.put("/{check_id}", response_model=FastnessCheckOut)
def update_check(
    check_id: int,
    payload: FastnessCheckUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    item = db.query(FastnessCheck).filter(FastnessCheck.id == check_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="色牢度抽检不存在")
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


@router.delete("/{check_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_check(
    check_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    item = db.query(FastnessCheck).filter(FastnessCheck.id == check_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="色牢度抽检不存在")
    db.delete(item)
    db.commit()
