import tempfile
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from app import Store
import ledger


class LedgerTest(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.store=Store(self.temp.name);self.workspace=self.store.workspace_id
        with self.store.connect() as c:
            ledger.patch_budget(c,self.workspace,'fixture',dict(limit={'amount':'10','currency':'USD'},maxConcurrentJobs=10,allowAutomaticRetries=False),0)
    def command(self,kind,data,key):
        with self.store.connect() as c:
            c.execute('BEGIN IMMEDIATE')
            return ledger.command(c,self.workspace,'fixture',kind,data,key)
    def reserve(self,key,amount='6'):
        return self.command('reserve',dict(money={'amount':amount,'currency':'USD'},budget_revision=1,expires=time.time()+300,job=key),key)
    def test_concurrent_reservations_never_exceed_limit(self):
        def run(key):
            try:return self.reserve(key)['reservation']
            except ledger.LedgerError:return 'denied'
        with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(run,['a','b']))
        self.assertEqual(results.count('denied'),1)
        with self.store.connect() as c:self.assertEqual(ledger.budget(c,self.workspace,'fixture')['data']['reserved']['amount'],'6')
    def test_uncertain_settlement_refund_and_idempotency(self):
        data=dict(money={'amount':'6','currency':'USD'},budget_revision=1,expires=time.time()+300,job='x')
        first=self.command('reserve',data,'stable');self.assertEqual(first,self.command('reserve',data,'stable'))
        with self.assertRaises(ledger.LedgerError):self.command('reserve',dict(data,job='changed'),'stable')
        identifier=first['reservation']
        self.command('uncertain',{'reservation':identifier},'uncertain')
        with self.assertRaises(ledger.LedgerError):self.command('release',{'reservation':identifier},'cancel')
        self.command('settle',dict(reservation=identifier,money={'amount':'4.5','currency':'USD'}),'settle')
        refund=dict(reservation=identifier,money={'amount':'1.5','currency':'USD'})
        result=self.command('refund',refund,'refund');self.assertEqual(result,self.command('refund',refund,'refund'))
        self.assertEqual(result['budget']['data']['netConfirmed']['amount'],'3')
        self.assertEqual(result['budget']['data']['reserved']['amount'],'0')
        with self.assertRaises(ledger.LedgerError):self.command('refund',dict(refund,money={'amount':'9','currency':'USD'}),'over-refund')
        self.assertEqual(Store(self.temp.name).workspace_id,self.workspace)
    def test_release_late_settlement_and_budget_lock(self):
        identifier=self.reserve('cancel')['reservation']
        self.command('release',{'reservation':identifier},'release')
        result=self.command('settle',dict(reservation=identifier,money={'amount':'6','currency':'USD'}),'late')
        self.assertEqual(result['budget']['data']['netConfirmed']['amount'],'6')
        with self.store.connect() as c:self.assertEqual(c.execute('SELECT state FROM reservations WHERE id=?',(identifier,)).fetchone()[0],'disputed')
        with self.assertRaises(ledger.LedgerError):self.command('settle',dict(reservation=identifier,money={'amount':'6','currency':'USD'}),'duplicate-provider-event')
        with self.store.connect() as c:
            with self.assertRaises(ledger.LedgerError) as exc:ledger.patch_budget(c,self.workspace,'fixture',dict(limit={'amount':'20','currency':'USD'},maxConcurrentJobs=1,allowAutomaticRetries=False),0)
            self.assertEqual(exc.exception.status,412)
    def test_overrun_is_visible_and_stops_new_reservations(self):
        identifier=self.reserve('x')['reservation']
        result=self.command('settle',dict(reservation=identifier,money={'amount':'12','currency':'USD'}),'overrun')
        self.assertEqual(result['budget']['data']['overrun']['amount'],'2')
        with self.assertRaises(ledger.LedgerError):self.reserve('y','1')

    def test_invalid_expiry_cannot_reserve(self):
        for expiry in [None,True,'tomorrow',float('nan'),float('inf')]:
            with self.subTest(expiry=expiry),self.assertRaises(ledger.LedgerError):
                self.command('reserve',dict(money={'amount':'1','currency':'USD'},budget_revision=1,expires=expiry,job='invalid'),'invalid')
        with self.store.connect() as c:self.assertEqual(c.execute('SELECT count(*) FROM reservations').fetchone()[0],0)
