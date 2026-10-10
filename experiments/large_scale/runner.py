"""N=200 supplement with immutable planning, append-only resume and RAM guards.

Usage: python -m experiments.large_scale.runner --preflight
       python -m experiments.large_scale.runner --run --priority-only
       python -m experiments.large_scale.runner --run
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import fcntl
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import platform
import random
import resource
import shutil
import subprocess
import sys

import psutil

from experiments.benchmark_runner import parse_stdout_json
from experiments.solver_registry import METHODS, REGISTRY, build_cli_command
from experiments.large_scale.resources import MIB, estimate_memory_mb, guarded_process, structural_counts
from src.common.validator import validate_positions

ROOT = Path(__file__).resolve().parents[2]
EXPERIMENT = 'nqueens_large_scale_n200'
RAW = ROOT / f'results/raw/benchmark_{EXPERIMENT}.jsonl'
META = ROOT / f'results/metadata/benchmark_{EXPERIMENT}_metadata.json'
PREFLIGHT = ROOT / f'results/metadata/benchmark_{EXPERIMENT}_preflight.json'
PRIORITY = ['sat_binary', 'cp_sat', 'cplex_cp']
RESOURCE_METHODS = ['sat_pairwise', 'sat_sequential', 'sat_commander', 'sat_product']
STATUSES = ['SAT', 'TIMEOUT', 'RESOURCE_LIMIT', 'BLOCKED_LICENSE', 'NOT_RUN_RESOURCE_POLICY',
            'ERROR', 'UNKNOWN', 'LICENSE_ERROR', 'MISSING_CP_ENGINE', 'ENVIRONMENT_ERROR', 'VALIDATION_ERROR']
NO_EXECUTION = {'BLOCKED_LICENSE', 'NOT_RUN_RESOURCE_POLICY'}
CONFIG = dict(experiment_id=EXPERIMENT, n=200, repetitions=5, methods=list(METHODS),
              sat_phase_policy='solver_default', random_seed=0, schedule_seed=2026,
              timeout=300, external_timeout=330, workers=1, warmup_n=4,
              scheduling='priority first trials; resource first trials; seeded blocks for remaining reps')


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def save_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')
    temp.replace(path)


def source_hashes():
    paths = sorted((ROOT/'src').rglob('*.py')) + [
        ROOT/'experiments/solver_registry.py', ROOT/'experiments/benchmark_runner.py',
        Path(__file__), ROOT/'experiments/large_scale/resources.py']
    return {str(p.relative_to(ROOT)): digest(p) for p in paths}


def primary_hashes():
    paths = sorted((ROOT/'results').rglob('*primary_full*'))
    paths += sorted((ROOT/'results/figures/full').glob('*'))
    paths += sorted((ROOT/'results/tables').glob('table0[1-6]*'))
    return {str(p.relative_to(ROOT)): digest(p) for p in paths if p.is_file()}


def check_primary(plan):
    for relative, expected in plan['primary_sha256'].items():
        if digest(ROOT/relative) != expected:
            raise ValueError(f'Primary artifact changed: {relative}')


def ensure_idle():
    blockers = []
    for p in psutil.process_iter(['pid', 'cmdline']):
        if p.pid == os.getpid():
            continue
        args = p.info['cmdline'] or []
        # Exact argv tokens, so a shell/inspection command containing these words is not a blocker.
        if any(a in {'experiments.benchmark_runner', 'experiments.large_scale.runner'} for a in args) or any(
                Path(a).name in {'cpoptimizer', 'pdflatex', 'xelatex', 'lualatex', 'tectonic', 'latexmk'} for a in args[:1]):
            blockers.append(p.pid)
    if blockers:
        raise RuntimeError(f'Other benchmark or LaTeX processes active: {blockers}')


def solver_env():
    env = os.environ.copy()
    env['PATH'] = str(ROOT/'.venv/bin') + os.pathsep + env.get('PATH', '')
    return env


def schedule():
    # Three first official trials are also the priority gate; no duplicated pilot results.
    result = [(m, 1) for m in PRIORITY + RESOURCE_METHODS + ['gurobi_mip', 'cplex_mip']]
    rng = random.Random(CONFIG['schedule_seed'])
    for rep in range(2, CONFIG['repetitions']+1):
        methods = list(METHODS)
        rng.shuffle(methods)
        result.extend((m, rep) for m in methods)
    return result


def preflight():
    ensure_idle()
    if PREFLIGHT.exists():
        raise FileExistsError('Frozen preflight already exists; use --run to resume')
    if RAW.exists():
        raise FileExistsError('Raw data exists without preflight; manual inspection required')
    from experiments.visualization.data_validator import validate_full_benchmark_dataset
    full = validate_full_benchmark_dataset(ROOT/'results/raw/benchmark_nqueens_primary_full.jsonl',
                                         ROOT/'results/metadata/benchmark_nqueens_primary_full_metadata.json')
    if not full['valid']:
        raise ValueError(f'Primary Full integrity failed: {full["problems"]}')
    v = psutil.virtual_memory()
    reserve = 2048.0
    # Use only 75% of the headroom above reserve, capped at 4 GiB. Refuse high-risk models.
    cap = min(4096.0, max(0, (v.available/MIB - reserve) * 0.75))
    if cap < 256:
        raise RuntimeError('Insufficient safe headroom for even the priority preflight; close memory-intensive applications')
    packages = {}
    for name in ['python-sat', 'ortools', 'gurobipy', 'docplex', 'cplex', 'psutil', 'numpy', 'pandas', 'matplotlib', 'seaborn']:
        packages[name] = importlib.metadata.version(name)
    runtime = dict(cpu=subprocess.check_output(['sysctl', '-n', 'machdep.cpu.brand_string'], text=True).strip(),
                   os=platform.platform(), architecture=platform.machine(), python=platform.python_version(),
                   total_ram_mb=v.total/MIB, available_ram_mb=v.available/MIB,
                   swap_used_mb=psutil.swap_memory().used/MIB, free_disk_mb=shutil.disk_usage(ROOT).free/MIB,
                   versions=packages,
                   rlimits={name: list(resource.getrlimit(getattr(resource, name))) for name in ['RLIMIT_AS', 'RLIMIT_RSS', 'RLIMIT_DATA']})
    availability = {}
    cli_config = dict(CONFIG)
    for method in METHODS:
        cmd = [sys.executable, '-m', REGISTRY[method]['module'], '--help']
        p = subprocess.run(cmd, cwd=ROOT, env=solver_env(), capture_output=True, text=True, timeout=20)
        availability[method] = {'cli_help_returncode': p.returncode}
        if p.returncode:
            raise RuntimeError(f'CLI/import failed for {method}: {p.stderr[-500:]}')
    # Current small boundary probes; never build or solve known-blocked N=200 MIP.
    licenses = {}
    for method, boundary in [('gurobi_mip', 45), ('cplex_mip', 32)]:
        p = subprocess.run(build_cli_command(method, boundary, cli_config), cwd=ROOT, env=solver_env(),
                           capture_output=True, text=True, timeout=30)
        data = parse_stdout_json(p.stdout)
        if not data or data['status'] != 'LICENSE_ERROR':
            raise RuntimeError(f'{method}: license environment differs from known limits; review plan before N=200')
        licenses[method] = dict(probe_n=boundary, status=data['status'], error=data.get('error'))
    # Actual N=4 warm-ups/import/engine checks. Stored outside official N=200 JSONL.
    warmups = []
    for method in PRIORITY + RESOURCE_METHODS:
        p = guarded_process(build_cli_command(method, 4, cli_config), cwd=ROOT, env=solver_env(),
                            timeout=30, memory_mb=cap, reserve_mb=reserve)
        data = parse_stdout_json(p['stdout'])
        if p['status'] or not data or data.get('status') != 'SAT' or not validate_positions(data['positions'], 4):
            raise RuntimeError(f'Warmup {method} failed: {p["status"]} {p["error_message"]}')
        warmups.append(dict(method_id=method, n=4, status=data['status'], valid=data['valid'],
                            process_wall_time=p['process_wall_time'], peak_memory_mb=p['peak_memory_mb']))
    estimates = {m: dict(**structural_counts(REGISTRY[m]['encoding'], 200),
                        estimated_memory_mb=estimate_memory_mb(REGISTRY[m]['encoding'], 200))
                 for m in METHODS if m.startswith('sat_')}
    policy = {}
    for m in METHODS:
        estimate = estimates.get(m, {}).get('estimated_memory_mb', 256.0)
        policy[m] = ('BLOCKED_LICENSE' if m in licenses else
                     'NOT_RUN_RESOURCE_POLICY' if estimate > cap else 'RUN')
    plan = dict(config=CONFIG, created_at_utc=now(), hardware=runtime, memory_cap_mb=cap,
                reserve_mb=reserve, memory_sample_seconds=0.1, availability=availability,
                license_evidence=licenses, warmups=warmups, structural_estimates=estimates,
                method_policy=policy, source_sha256=source_hashes(), primary_sha256=primary_hashes(),
                source_commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
                expected_keys=[[m, 200, rep] for m, rep in schedule()],
                memory_policy_note='Polled tree RSS, not a hard quota. Conservative estimates refuse large models. Stop on cap or system reserve; a resource failure disables further trials of that method.',
                sat_capabilities='Glucose3 wrappers have no native wall-time/seed option: solver_default, no set_phases, external 330s whole-process limit. Exact solvers receive 300s, workers=1, seed=0.',
                timing_definition='pipeline_total_time = unchanged solver total_time; excludes interpreter startup and parent validation; process_wall_time includes monitor/cleanup')
    plan['configuration_fingerprint'] = fingerprint({k: plan[k] for k in
        ['config', 'memory_cap_mb', 'reserve_mb', 'memory_sample_seconds', 'method_policy', 'source_sha256']})
    save_json(PREFLIGHT, plan)
    print(json.dumps({k: plan[k] for k in ['hardware', 'memory_cap_mb', 'method_policy', 'structural_estimates']}, indent=2), flush=True)


def read_records(path):
    if not path.exists():
        return []
    raw = path.read_bytes()
    if raw and not raw.endswith(b'\n'):
        raise ValueError('JSONL lacks a terminating newline; refusing unsafe append')
    return [json.loads(line) for line in raw.splitlines() if line.strip()]


def validate_records(records, plan, require_complete=False):
    expected = {tuple(k) for k in plan['expected_keys']}
    seen, ids = set(), set()
    for r in records:
        key = (r['method_id'], r['n'], r['repetition'])
        if key not in expected or key in seen or r['run_id'] in ids:
            raise ValueError(f'Duplicate or unexpected trial: {key}')
        seen.add(key); ids.add(r['run_id'])
        if r['experiment_id'] != EXPERIMENT or r['configuration_fingerprint'] != plan['configuration_fingerprint']:
            raise ValueError('Experiment/fingerprint mismatch')
        if r['run_id'] != f'{EXPERIMENT}_{key[0]}_n200_r{key[2]}' or r.get('is_warmup'):
            raise ValueError('Run identity/warm-up mismatch')
        for name, wanted in [('workers', 1), ('random_seed', 0), ('timeout', 300), ('external_timeout', 330)]:
            if r.get(name) != wanted:
                raise ValueError(f'Configuration mismatch: {name}')
        policy = 'solver_default' if key[0].startswith('sat_') else None
        if r.get('phase_policy') != policy or r['status'] not in STATUSES:
            raise ValueError('Invalid phase policy or status')
        for field in ['pipeline_total_time', 'process_wall_time', 'peak_memory_mb', 'model_build_time', 'solve_time']:
            val = r.get(field)
            if val is not None and (isinstance(val, bool) or not isinstance(val, (int,float)) or not math.isfinite(val) or val < 0):
                raise ValueError(f'Invalid timing/memory field: {field}')
        if r['status'] in NO_EXECUTION:
            if r['executed'] or any(r.get(k) is not None for k in ['pipeline_total_time','process_wall_time','peak_memory_mb']):
                raise ValueError('Unexecuted trial has runtime')
            if r['status'] == 'BLOCKED_LICENSE' and key[0] not in plan['license_evidence']:
                raise ValueError('Unsubstantiated license block')
        elif not r['executed']:
            raise ValueError('Executed outcome marked unexecuted')
        if r['status'] == 'SAT':
            if r['valid'] is not True or r['pipeline_total_time'] is None or not validate_positions(r['positions'], 200):
                raise ValueError('SAT record without independently valid solution/timing')
        if r['status'] in {'TIMEOUT', 'RESOURCE_LIMIT'} and r['pipeline_total_time'] is not None:
            raise ValueError('Failure must not contain successful pipeline runtime')
    missing = expected-seen
    if require_complete and missing:
        raise ValueError(f'Missing {len(missing)} trials')
    return dict(expected=len(expected), actual=len(records), unique_keys=len(seen),
                missing_keys=[list(k) for k in sorted(missing)], duplicates=0,
                status_counts=dict(Counter(r['status'] for r in records)),
                executed=sum(r['executed'] for r in records))


def execute_trial(method, rep, plan, earlier):
    now_available = psutil.virtual_memory().available / MIB
    r = dict(experiment_id=EXPERIMENT, method_id=method, method_family=REGISTRY[method]['method_family'],
             run_id=f'{EXPERIMENT}_{method}_n200_r{rep}', n=200, repetition=rep, is_warmup=False,
             status='ERROR', valid=None, executed=False, pipeline_total_time=None,
             process_wall_time=None, model_build_time=None, solve_time=None,
             primary_variables=None, auxiliary_variables=None, total_variables=None, clauses=None,
             constraints=None, peak_memory_mb=None, phase_policy='solver_default' if method.startswith('sat_') else None,
             timeout=300, external_timeout=330, workers=1, random_seed=0,
             configuration_fingerprint=plan['configuration_fingerprint'], error_message=None,
             positions=None, timestamp_utc=now(), available_memory_before_mb=now_available,
             memory_cap_mb=plan['memory_cap_mb'])
    policy = plan['method_policy'][method]
    resource_stop = any(x['method_id']==method and x['status']=='RESOURCE_LIMIT' for x in earlier)
    estimate = plan['structural_estimates'].get(method, {}).get('estimated_memory_mb', 256.0)
    if policy != 'RUN' or resource_stop or now_available < plan['reserve_mb']+estimate:
        r['status'] = policy if policy != 'RUN' else 'NOT_RUN_RESOURCE_POLICY'
        r['error_message'] = ('Verified current restricted MIP license' if policy == 'BLOCKED_LICENSE' else
                              'Frozen preflight estimate exceeds cap' if policy != 'RUN' else
                              'Earlier trial hit resource limit' if resource_stop else 'Insufficient current memory headroom')
        return r
    r['executed'] = True
    cmd = build_cli_command(method, 200, CONFIG)
    r['command'] = ['.venv/bin/python']+cmd[1:]
    outcome = guarded_process(cmd, cwd=ROOT, env=solver_env(), timeout=330,
                              memory_mb=plan['memory_cap_mb'], reserve_mb=plan['reserve_mb'])
    for name in ['process_wall_time', 'peak_memory_mb', 'minimum_available_memory_mb', 'memory_measurement', 'memory_sample_seconds']:
        r[name] = outcome[name]
    if outcome['status']:
        r.update(status=outcome['status'], error_message=outcome['error_message'])
        return r
    data = parse_stdout_json(outcome['stdout'])
    if not data:
        r['error_message'] = f'No solver JSON; returncode={outcome["returncode"]}; stderr={outcome["stderr"][-500:]}'
        return r
    r.update(status=data['status'], valid=data.get('valid'), positions=data.get('positions'),
             native_status=data.get('native_status'), statistics=data.get('statistics', {}),
             error_message=data.get('error'), model_build_time=data.get('encoding_time', data.get('build_time')),
             solve_time=data.get('solve_time'))
    for field in ['primary_variables', 'auxiliary_variables', 'total_variables', 'clauses', 'constraints',
                  'encoding_time', 'build_time', 'load_time', 'search_time', 'decode_validate_time']:
        r[field] = data.get(field)
    if method in {'cp_sat', 'cplex_cp'}:
        r['total_variables'] = data.get('decision_variables')
    if r['status'] == 'SAT':
        if outcome['returncode'] or r['valid'] is not True or not validate_positions(r['positions'], 200):
            r.update(status='VALIDATION_ERROR', valid=False, error_message='Parent common validation/exit check failed')
        else:
            r['pipeline_total_time'] = data['total_time']
            r['queen_count'] = len(r['positions'])
    return r


def run(priority_only=False):
    # Advisory lock prevents two supplementary runners; primary process check is separate.
    lock_path = ROOT/'results/metadata/.n200.lock'
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        ensure_idle()
        plan = json.loads(PREFLIGHT.read_text())
        if plan['config'] != CONFIG or plan['source_sha256'] != source_hashes():
            raise ValueError('Frozen source or configuration changed; refusing resume')
        check_primary(plan)
        records = read_records(RAW)
        integrity = validate_records(records, plan)
        completed = {(r['method_id'], r['repetition']) for r in records}
        print(f'{EXPERIMENT}: {len(records)}/{integrity["expected"]} already recorded', flush=True)
        RAW.parent.mkdir(parents=True, exist_ok=True)
        with RAW.open('a') as output:
            for method, rep in schedule():
                if priority_only and (method not in PRIORITY or rep != 1):
                    continue
                if (method, rep) in completed:
                    continue
                print(f'RUN {method} N=200 repetition={rep}', flush=True)
                record = execute_trial(method, rep, plan, records)
                validate_records(records+[record], plan)
                output.write(json.dumps(record, allow_nan=False)+'\n')
                output.flush(); os.fsync(output.fileno())
                records.append(record)
                print(f'  {record["status"]} time={record["pipeline_total_time"]} peak_MiB={record["peak_memory_mb"]} [{len(records)}/{integrity["expected"]}]', flush=True)
        check_primary(plan)
        integrity = validate_records(records, plan, require_complete=not priority_only)
        save_json(META, dict(experiment_id=EXPERIMENT, configuration_fingerprint=plan['configuration_fingerprint'],
                             config=CONFIG, hardware=plan['hardware'], memory_cap_mb=plan['memory_cap_mb'], reserve_mb=plan['reserve_mb'],
                             preflight=str(PREFLIGHT.relative_to(ROOT)), completed_at_utc=now(), integrity=integrity,
                             primary_sha256_before=plan['primary_sha256'], primary_sha256_after=primary_hashes(),
                             raw_sha256=digest(RAW), complete=not integrity['missing_keys'],
                             source_sha256=plan['source_sha256'], timing_definition=plan['timing_definition'],
                             sat_capabilities=plan['sat_capabilities']))
        print(json.dumps(integrity, indent=2), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--preflight', action='store_true')
    group.add_argument('--run', action='store_true', help='Append only missing trials; never overwrite')
    parser.add_argument('--priority-only', action='store_true', help='Run first official trial for each priority method')
    args = parser.parse_args()
    if args.preflight:
        preflight()
    else:
        run(args.priority_only)


if __name__ == '__main__':
    main()
