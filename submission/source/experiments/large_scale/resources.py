"""Analytical CNF sizing and a polled process-tree resource guard."""
from __future__ import annotations

import math
import os
import signal
import subprocess
import tempfile
import time
from functools import lru_cache
from pathlib import Path

import psutil

MIB = 1024 ** 2


@lru_cache(None)
def amo_counts(encoding: str, m: int) -> tuple[int, int]:
    """Return auxiliaries, clauses for the exact variants in src/sat/encodings."""
    if m <= 1:
        return 0, 0
    if encoding == 'pairwise':
        return 0, m * (m - 1) // 2
    if encoding == 'binary':
        bits = (m - 1).bit_length()
        return bits, m * bits
    if encoding == 'sequential':
        return m - 1, 3 * m - 4
    if encoding == 'commander':
        if m <= 3:
            return 0, m * (m - 1) // 2
        sizes = [min(3, m - offset) for offset in range(0, m, 3)]
        aux, clauses = amo_counts(encoding, len(sizes))
        return len(sizes) + aux, m + sum(k * (k - 1) // 2 for k in sizes) + clauses
    if encoding == 'product':
        p = math.isqrt(m)
        p += p * p < m
        q = (m + p - 1) // p
        return p + q, 2 * m + p * (p - 1) // 2 + q * (q - 1) // 2
    raise ValueError(f'Unknown encoding: {encoding}')


def structural_counts(encoding: str, n: int) -> dict:
    if n < 1:
        raise ValueError('n must be positive')
    # 2N rows/columns; both diagonal families: two length-N and four of 2..N-1.
    groups = [n] * (2 * n)
    if n >= 2:
        groups += [n] * 2 + [m for m in range(2, n) for _ in range(4)]
    counts = [amo_counts(encoding, m) for m in groups]
    auxiliary = sum(a for a, _ in counts)
    clauses = 2 * n + sum(c for _, c in counts)
    return dict(primary_variables=n*n, auxiliary_variables=auxiliary,
                total_variables=n*n+auxiliary, clauses=clauses)


def estimate_memory_mb(encoding: str, n: int) -> float:
    """Conservative planning estimate, not measured RSS or a guaranteed bound.

    Each Python binary clause holds a list header, two pointers and up to two
    PyLongs (~136 B incl. the outer pointer on this interpreter). Budget 320 B
    per clause for list over-allocation, allocator overhead and native SAT copy;
    add 64 B per variable and 128 MiB for imports/search. Learned clauses can
    exceed this estimate, hence runtime tree-RSS and system-reserve monitoring.
    """
    s = structural_counts(encoding, n)
    return (320 * s['clauses'] + 64 * s['total_variables']) / MIB + 128


def process_snapshot(root: psutil.Process) -> tuple[int, list[psutil.Process]]:
    try:
        members = [root] + root.children(recursive=True)
    except psutil.NoSuchProcess:
        return 0, []
    rss = 0
    living = []
    for member in members:
        try:
            rss += member.memory_info().rss
            living.append(member)
        except psutil.NoSuchProcess:
            pass
    return rss, living


def cleanup_group(proc: subprocess.Popen, known: list[psutil.Process]) -> None:
    """Only terminate this trial's newly-created process group/descendants."""
    try:
        os.killpg(proc.pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    for child in known:
        try:
            child.terminate()
        except psutil.NoSuchProcess:
            pass
    try:
        proc.wait(timeout=1)
    except subprocess.TimeoutExpired:
        pass
    try:
        os.killpg(proc.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    for child in known:
        try:
            if child.is_running():
                child.kill()
        except psutil.NoSuchProcess:
            pass
    proc.wait(timeout=3)
    psutil.wait_procs(known, timeout=1)


def guarded_process(command: list[str], *, cwd: Path, env: dict,
                    timeout: float, memory_mb: float, reserve_mb: float,
                    sample_seconds: float = 0.1) -> dict:
    """Run one process group, recording sampled tree RSS and resource reasons.

    This is a polling guard, not an OS hard memory quota. Native macOS RLIMIT_RSS
    is not used as a guarantee. The preflight refuses risky models separately.
    Output is spooled to files so pipe back-pressure cannot stall the solver.
    """
    start = time.perf_counter()
    peak = 0
    minimum_available = None
    seen = {}
    outcome = None
    error = None
    with tempfile.TemporaryFile() as stdout, tempfile.TemporaryFile() as stderr:
        proc = subprocess.Popen(command, cwd=cwd, env=env, stdout=stdout,
                                stderr=stderr, start_new_session=True)
        root = psutil.Process(proc.pid)
        try:
            while proc.poll() is None:
                try:
                    rss, members = process_snapshot(root)
                    for member in members:
                        seen[member.pid] = member
                    available = psutil.virtual_memory().available / MIB
                except psutil.AccessDenied:
                    outcome, error = 'RESOURCE_LIMIT', 'Memory monitoring became unavailable'
                    break
                peak = max(peak, rss)
                minimum_available = available if minimum_available is None else min(minimum_available, available)
                if rss / MIB > memory_mb or available < reserve_mb:
                    outcome = 'RESOURCE_LIMIT'
                    error = f'Tree RSS {rss/MIB:.1f} MiB (cap {memory_mb:.1f}); available {available:.1f} MiB (reserve {reserve_mb:.1f})'
                    break
                if time.perf_counter() - start >= timeout:
                    outcome, error = 'TIMEOUT', f'External subprocess timeout ({timeout}s)'
                    break
                time.sleep(sample_seconds)
        finally:
            cleanup_group(proc, list(seen.values()))
        stdout.seek(0)
        stderr.seek(0)
        return dict(status=outcome, error_message=error, returncode=proc.returncode,
                    stdout=stdout.read().decode('utf-8', errors='replace'),
                    stderr=stderr.read().decode('utf-8', errors='replace'),
                    process_wall_time=time.perf_counter()-start,
                    peak_memory_mb=peak/MIB if peak else None,
                    minimum_available_memory_mb=minimum_available,
                    memory_measurement='sampled sum of parent and descendant RSS; MiB; may double-count shared pages',
                    memory_sample_seconds=sample_seconds)
