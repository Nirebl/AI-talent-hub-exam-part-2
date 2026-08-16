from __future__ import annotations

import argparse
import asyncio
import math
import statistics
from time import perf_counter
from uuid import uuid4

import httpx


SAFE_TEXTS = (
    "Как поменять пароль?",
    "Как изменить email в аккаунте?",
    "Как отключить подписку?",
    "После обновления приложение падает",
)

HUMAN_TEXTS = (
    "С моей карты списали деньги без моего согласия",
    "Хочу вернуть деньги за списание",
)


def percentile(values: list[float], q: float) -> float:
    if not values:
        return 0.0

    ordered = sorted(values)
    index = max(
        0,
        min(
            len(ordered) - 1,
            math.ceil(q * len(ordered)) - 1,
        ),
    )
    return ordered[index]


async def run_request(
    client: httpx.AsyncClient,
    semaphore: asyncio.Semaphore,
    *,
    index: int,
    mode: str,
) -> tuple[int, float]:
    if mode == "safe":
        text = SAFE_TEXTS[index % len(SAFE_TEXTS)]
    elif mode == "human":
        text = HUMAN_TEXTS[index % len(HUMAN_TEXTS)]
    else:
        pool = SAFE_TEXTS + HUMAN_TEXTS
        text = pool[index % len(pool)]

    payload = {
        "external_id": f"load-{uuid4()}",
        "channel": "web",
        "text": text,
        "user_id": f"load-user-{index}",
        "metadata": {
            "language": "ru",
            "client": "web",
            "app_version": "load-test",
        },
    }

    async with semaphore:
        started = perf_counter()
        response = await client.post("/tickets", json=payload)
        elapsed_ms = (perf_counter() - started) * 1000
        return response.status_code, elapsed_ms


async def run(args: argparse.Namespace) -> int:
    timeout = httpx.Timeout(args.timeout)
    semaphore = asyncio.Semaphore(args.concurrency)

    async with httpx.AsyncClient(
        base_url=args.base_url,
        timeout=timeout,
    ) as client:
        for index in range(args.warmup):
            await run_request(
                client,
                semaphore,
                index=index,
                mode=args.mode,
            )

        started = perf_counter()
        results = await asyncio.gather(
            *(
                run_request(
                    client,
                    semaphore,
                    index=index,
                    mode=args.mode,
                )
                for index in range(args.requests)
            )
        )
        duration = perf_counter() - started

    statuses = [status for status, _ in results]
    latencies = [latency for _, latency in results]
    successes = sum(
        1
        for status in statuses
        if status in (200, 201)
    )
    failures = len(results) - successes

    print(f"requests={len(results)}")
    print(f"concurrency={args.concurrency}")
    print(f"duration_s={duration:.3f}")
    print(f"throughput_rps={len(results) / duration:.2f}")
    print(f"successes={successes}")
    print(f"failures={failures}")
    print(f"latency_mean_ms={statistics.mean(latencies):.2f}")
    print(f"latency_p50_ms={percentile(latencies, 0.50):.2f}")
    print(f"latency_p95_ms={percentile(latencies, 0.95):.2f}")
    print(f"latency_p99_ms={percentile(latencies, 0.99):.2f}")
    print(f"latency_max_ms={max(latencies):.2f}")
    under_target = sum(
        1
        for latency in latencies
        if latency <= args.target_ms
    )
    print(
        f"under_{args.target_ms:g}ms_pct="
        f"{under_target / len(latencies) * 100:.2f}"
    )

    return 0 if failures == 0 else 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--base-url",
        default="http://127.0.0.1:8000",
    )
    parser.add_argument(
        "--requests",
        type=int,
        default=1000,
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=50,
    )
    parser.add_argument(
        "--warmup",
        type=int,
        default=20,
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=10.0,
    )
    parser.add_argument(
        "--target-ms",
        type=float,
        default=500.0,
    )
    parser.add_argument(
        "--mode",
        choices=("safe", "human", "mixed"),
        default="mixed",
    )
    return parser.parse_args()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(run(parse_args())))
