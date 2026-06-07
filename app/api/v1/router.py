from fastapi import APIRouter

from app.api.v1 import (
    audit,
    auth,
    documents,
    health,
    messages,
    orders,
    partners,
    payments,
    requests,
    roles,
    services,
    tasks,
    users,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(services.router)
api_router.include_router(requests.router)
api_router.include_router(orders.router)
api_router.include_router(messages.router)
api_router.include_router(tasks.router)
api_router.include_router(payments.router)
api_router.include_router(documents.router)
api_router.include_router(users.router)
api_router.include_router(roles.router)
api_router.include_router(partners.router)
api_router.include_router(audit.router)
