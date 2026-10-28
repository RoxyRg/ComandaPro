#!/usr/bin/env python3
"""Carga ligera de la API local. No es una prueba de capacidad de producción."""
from __future__ import annotations

import argparse
import json
import statistics
import time
from concurrent.futures import ThreadPoolExecutor
from collections import Counter
from urllib.error import URLError, HTTPError
from urllib.request import urlopen


def request_once(url: str, timeout: float) -> tuple[int | str, float]:
    started = time.perf_counter()
    try:
        with urlopen(url, timeout=timeout) as response:
            response.read()
            return response.status, (time.perf_counter() - started) * 1000
    except HTTPError as exc:
        return exc.code, (time.perf_counter() - started) * 1000
    except (URLError, TimeoutError, OSError):
        return "ERROR", (time.perf_counter() - started) * 1000


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:8080/api/health")
    parser.add_argument("--requests", type=int, default=40)
    parser.add_argument("--concurrency", type=int, default=4)
    parser.add_argument("--timeout", type=float, default=10)
    args = parser.parse_args()
    if args.requests < 1 or args.concurrency < 1 or args.timeout <= 0:
        parser.error("requests y concurrency deben ser >= 1; timeout debe ser > 0")

    with ThreadPoolExecutor(max_workers=args.concurrency) as pool:
        results = list(pool.map(lambda _: request_once(args.url, args.timeout), range(args.requests)))

    statuses = Counter(status for status, _ in results)
    timings = sorted(duration for _, duration in results)
    percentile_95 = timings[min(len(timings) - 1, max(0, int(len(timings) * 0.95) - 1))]
    print("ComandaPro — prueba de carga controlada")
    print("URL:", args.url)
    print("Total de peticiones:", len(results))
    print("Concurrencia máxima:", args.concurrency)
    print("Resultados HTTP:", dict(statuses))
    print(f"Tiempo promedio: {statistics.mean(timings):.2f} ms")
    print(f"Tiempo máximo: {max(timings):.2f} ms")
    print(f"Percentil 95: {percentile_95:.2f} ms")
    failed = sum(count for status, count in statuses.items() if status != 200)
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
