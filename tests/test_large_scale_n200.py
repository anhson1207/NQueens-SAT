"""Protocol tests use synthetic temporary records and tiny subprocesses only."""
import copy
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from experiments.large_scale.resources import guarded_process, structural_counts
from experiments.large_scale.runner import (
    CONFIG, EXPERIMENT, METHODS, ROOT, check_primary, digest, execute_trial,
    fingerprint, read_records, schedule, validate_records,
)


def plan_fixture():
    return dict(expected_keys=[[m,200,r] for m,r in schedule()],
                configuration_fingerprint='test-fingerprint', method_policy={m:'RUN' for m in METHODS},
                license_evidence={'gurobi_mip':{},'cplex_mip':{}},
                structural_estimates={}, memory_cap_mb=512, reserve_mb=1)


def record_fixture(method='sat_binary', rep=1):
    return dict(experiment_id=EXPERIMENT, method_id=method, n=200, repetition=rep,
                run_id=f'{EXPERIMENT}_{method}_n200_r{rep}', is_warmup=False,
                status='TIMEOUT', executed=True, valid=None, pipeline_total_time=None,
                process_wall_time=330, model_build_time=None, solve_time=None,
                peak_memory_mb=100, phase_policy='solver_default' if method.startswith('sat_') else None,
                workers=1, random_seed=0, timeout=300, external_timeout=330,
                configuration_fingerprint='test-fingerprint', positions=None)


class TestN200Structure(unittest.TestCase):
    def test_analytical_counts_match_actual_small_encoders(self):
        from src.sat.encodings import binary, sequential, commander, product, pairwise
        for module in [pairwise,binary,sequential,commander,product]:
            name=module.__name__.split('.')[-1]
            for n in [1,2,4,8]:
                actual=getattr(module,f'encode_nqueens_{name}')(n)
                cnf,total=(actual,n*n) if name=='pairwise' else actual
                predicted=structural_counts(name,n)
                self.assertEqual(predicted['clauses'],len(cnf))
                self.assertEqual(predicted['total_variables'],total)
    def test_n200_pairwise_without_allocating_cnf(self):
        s=structural_counts('pairwise',200)
        self.assertEqual(s['primary_variables'],40000)
        self.assertEqual(s['clauses'],2*200+200*200*199+200*199*(399)//3)
    def test_priority_schedule_and_exact_coverage(self):
        self.assertEqual(schedule()[:3],[('sat_binary',1),('cp_sat',1),('cplex_cp',1)])
        self.assertEqual(len(schedule()),45)
        self.assertEqual(len(set(schedule())),45)


class TestN200Integrity(unittest.TestCase):
    def test_completed_failure_is_preserved_on_resume(self):
        r=record_fixture()
        plan=plan_fixture()
        result=validate_records([r],plan)
        self.assertEqual(result['actual'],1)
        self.assertEqual(len(result['missing_keys']),44)
        self.assertNotIn(['sat_binary',200,1],result['missing_keys'])
    def test_duplicate_and_fingerprint_mismatch_rejected(self):
        r=record_fixture()
        with self.assertRaises(ValueError): validate_records([r,r],plan_fixture())
        r['configuration_fingerprint']='changed'
        with self.assertRaises(ValueError): validate_records([r],plan_fixture())
    def test_wrong_experiment_or_phase_rejected(self):
        for field,value in [('experiment_id','primary_full'),('phase_policy','legacy'),('workers',2)]:
            r=record_fixture();r[field]=value
            with self.assertRaises(ValueError): validate_records([r],plan_fixture())
    def test_invalid_sat_and_fake_failure_time_rejected(self):
        r=record_fixture();r.update(status='SAT',valid=True,positions=[[0,0]]*200,pipeline_total_time=1)
        with self.assertRaises(ValueError): validate_records([r],plan_fixture())
        r=record_fixture();r['pipeline_total_time']=300
        with self.assertRaises(ValueError): validate_records([r],plan_fixture())
    def test_policy_has_no_execution_or_time(self):
        plan=plan_fixture();plan['method_policy']['sat_pairwise']='NOT_RUN_RESOURCE_POLICY'
        with patch('experiments.large_scale.runner.guarded_process') as launch:
            r=execute_trial('sat_pairwise',1,plan,[])
        launch.assert_not_called()
        self.assertFalse(r['executed']);self.assertIsNone(r['pipeline_total_time'])
        validate_records([r],plan)
    def test_license_block_never_launches(self):
        plan=plan_fixture();plan['method_policy']['cplex_mip']='BLOCKED_LICENSE'
        with patch('experiments.large_scale.runner.guarded_process') as launch:
            r=execute_trial('cplex_mip',1,plan,[])
        launch.assert_not_called();validate_records([r],plan)
    def test_malformed_or_truncated_jsonl_refuses_resume(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'data.jsonl'
            for content in ['{broken}\n','{}']:
                p.write_text(content)
                with self.assertRaises(ValueError): read_records(p)
    def test_primary_checksum_change_detected(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'full.jsonl';p.write_text('original')
            plan={'primary_sha256':{str(p):digest(p)}}
            check_primary(plan);p.write_text('changed')
            with self.assertRaises(ValueError): check_primary(plan)
    def test_resource_stop_disables_remaining_method_trials(self):
        first=record_fixture();first['status']='RESOURCE_LIMIT'
        with patch('experiments.large_scale.runner.guarded_process') as launch:
            r=execute_trial('sat_binary',2,plan_fixture(),[first])
        launch.assert_not_called();self.assertEqual(r['status'],'NOT_RUN_RESOURCE_POLICY')


class TestN200ResourceGuard(unittest.TestCase):
    def test_subprocess_success_is_captured(self):
        r=guarded_process([sys.executable,'-c','print("ok")'],cwd=ROOT,env=os.environ.copy(),timeout=5,memory_mb=2048,reserve_mb=0)
        self.assertIsNone(r['status']);self.assertEqual(r['stdout'].strip(),'ok')
    def test_timeout_and_child_cleanup(self):
        import psutil
        code='import subprocess,sys,time; p=subprocess.Popen([sys.executable,"-c","import time; time.sleep(30)"]); print(p.pid,flush=True); time.sleep(30)'
        r=guarded_process([sys.executable,'-c',code],cwd=ROOT,env=os.environ.copy(),timeout=0.5,memory_mb=2048,reserve_mb=0)
        self.assertEqual(r['status'],'TIMEOUT')
        pid=int(r['stdout'].strip())
        self.assertTrue(not psutil.pid_exists(pid) or psutil.Process(pid).status()==psutil.STATUS_ZOMBIE)
    def test_resource_limit_not_timeout(self):
        r=guarded_process([sys.executable,'-c','import time; x=bytearray(32*1024*1024); time.sleep(20)'],cwd=ROOT,env=os.environ.copy(),timeout=5,memory_mb=1,reserve_mb=0)
        self.assertEqual(r['status'],'RESOURCE_LIMIT')


if __name__=='__main__': unittest.main()
