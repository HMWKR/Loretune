"""Budget display distinguishes estimated usage from confirmed charges."""
from pathlib import Path
import subprocess
import unittest


class BudgetSummaryUITest(unittest.TestCase):
    def test_estimate_is_visible_only_when_recorded(self):
        source = (Path(__file__).resolve().parents[1] / 'index.html').read_text()
        code = source[source.index('function showBudget()'):source.index('async function loadBudgetLedger()')]
        script = r'''
const assert=require('node:assert/strict');
let budgetProject,budgetRevision;const node={innerHTML:''};
const $=()=>node,song=()=> 'song',esc=x=>String(x),creatorDiagnostic=()=>'';
const data={scope:'project:p',limit:{amount:'10',currency:'USD'},available:{amount:'9.9'},netConfirmed:{amount:'0'},reserved:{amount:'0'},netEstimated:{amount:'0.1',currency:'USD'},overrun:{amount:'0'},maxConcurrentJobs:1};
const state={project_ids:{song:'p'},budgets:[{revision:1,data}]};
''' + code + r'''
showBudget();assert.match(node.innerHTML,/확인된 사용액 0/);assert.match(node.innerHTML,/사용량 기준 추정액 0.1 USD · 실제 청구 미확인/);
data.netEstimated.amount='0';showBudget();assert.doesNotMatch(node.innerHTML,/사용량 기준 추정액/);
data.uncertainReservations=1;showBudget();assert.match(node.innerHTML,/미확정 비용 1건/);assert.match(node.innerHTML,/이 예산의 새 공급자 작업 전에 비용을 확인/);
data.uncertainReservations=0;showBudget();assert.doesNotMatch(node.innerHTML,/미확정 비용/);
'''
        result = subprocess.run(['node', '-e', script], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
