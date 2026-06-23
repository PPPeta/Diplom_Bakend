"""Тонкая обёртка над SDK ЮKassa (пакет ``yookassa``).

SDK импортируется лениво — приложение поднимается даже без установленного
пакета или ненастроенного магазина. SDK синхронный, поэтому сетевые вызовы
выполняем в пуле потоков через ``asyncio.to_thread``.
"""
from __future__ import annotations

import asyncio
import uuid
from decimal import Decimal
from typing import Any

from app.core.config import settings


class YooKassaError(RuntimeError):
    """Платёжный провайдер недоступен или вернул ошибку."""


def _configure() -> None:
    if not settings.yookassa_enabled:
        raise YooKassaError(
            "ЮKassa не настроена: задайте YOOKASSA_SHOP_ID и YOOKASSA_SECRET_KEY."
        )
    try:
        from yookassa import Configuration
    except ImportError as exc:  # pragma: no cover - зависит от окружения
        raise YooKassaError(
            "Пакет 'yookassa' не установлен. Добавьте его в requirements.txt."
        ) from exc
    Configuration.configure(
        settings.YOOKASSA_SHOP_ID, settings.YOOKASSA_SECRET_KEY
    )


def _create_payment_sync(
    amount: Decimal,
    description: str,
    return_url: str,
    metadata: dict[str, Any],
) -> dict[str, Any]:
    _configure()
    from yookassa import Payment as YkPayment

    payload = {
        "amount": {
            "value": f"{amount:.2f}",
            "currency": settings.YOOKASSA_CURRENCY,
        },
        "capture": True,
        "confirmation": {"type": "redirect", "return_url": return_url},
        "description": description,
        "metadata": metadata,
    }
    obj = YkPayment.create(payload, str(uuid.uuid4()))
    confirmation = getattr(obj, "confirmation", None)
    return {
        "id": obj.id,
        "status": obj.status,
        "confirmation_url": getattr(confirmation, "confirmation_url", None),
    }


def _get_payment_sync(external_id: str) -> dict[str, Any]:
    _configure()
    from yookassa import Payment as YkPayment

    obj = YkPayment.find_one(external_id)
    return {
        "id": obj.id,
        "status": obj.status,
        "paid": bool(getattr(obj, "paid", False)),
    }


async def create_payment(
    amount: Decimal,
    description: str,
    return_url: str,
    metadata: dict[str, Any],
) -> dict[str, Any]:
    try:
        return await asyncio.to_thread(
            _create_payment_sync, amount, description, return_url, metadata
        )
    except YooKassaError:
        raise
    except Exception as exc:  # pragma: no cover - сетевые/SDK ошибки
        raise YooKassaError(
            f"Ошибка ЮKassa при создании платежа: {exc}"
        ) from exc


async def get_payment(external_id: str) -> dict[str, Any]:
    try:
        return await asyncio.to_thread(_get_payment_sync, external_id)
    except YooKassaError:
        raise
    except Exception as exc:  # pragma: no cover - сетевые/SDK ошибки
        raise YooKassaError(
            f"Ошибка ЮKassa при запросе статуса: {exc}"
        ) from exc
