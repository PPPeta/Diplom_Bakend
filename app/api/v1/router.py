from fastapi import APIRouter

from app.api.v1 import (
    audit,
    auth,
    health,
    orders,
    payments,
    requests,
    services,
    tasks,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(services.router)
api_router.include_router(requests.router)
api_router.include_router(orders.router)
api_router.include_router(tasks.router)
api_router.include_router(payments.router)
api_router.include_router(audit.router)
