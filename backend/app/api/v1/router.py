from fastapi import APIRouter

from app.api.v1 import actions, findings, reports, scans, targets

router = APIRouter()
router.include_router(targets.router, prefix="/targets", tags=["Targets"])
router.include_router(scans.router, prefix="/scans", tags=["Scans"])
router.include_router(findings.router, prefix="/findings", tags=["Findings"])
router.include_router(reports.router, prefix="/reports", tags=["Reports"])
router.include_router(actions.router, prefix="/actions", tags=["Actions"])
