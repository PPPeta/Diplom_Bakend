from fastapi import HTTPException, Request, status

from app.core.config import settings
from app.db.redis import redis_client


async def rate_limit_login(request: Request) -> None:
    """Ограничивает число попыток входа с одного IP за окно времени.

    Используем Redis: счётчик на ключ ratelimit:login:{ip}.
    При первом запросе в окне ставим TTL. Если превысили
    лимит — отвечаем 429 Too Many Requests.
    """
    # Идентифицируем клиента по IP-адресу.
    client_ip = request.client.host if request.client else "unknown"
    key = f"ratelimit:login:{client_ip}"

    # INCR создаёт ключ со значением 1, если его не было.
    attempts = await redis_client.incr(key)
    if attempts == 1:
        # Первый запрос в окне — задаём срок жизни счётчика.
        await redis_client.expire(key, settings.LOGIN_RATE_LIMIT_WINDOW_SECONDS)

    if attempts > settings.LOGIN_RATE_LIMIT_MAX_ATTEMPTS:
        retry_after = await redis_client.ttl(key)
        # TTL может вернуть -1/-2, если ключ без срока — подстрахуемся.
        if retry_after < 0:
            retry_after = settings.LOGIN_RATE_LIMIT_WINDOW_SECONDS
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Слишком много попыток входа. Повторите через {retry_after} сек.",
            headers={"Retry-After": str(retry_after)},
        )
