"""Fenced, server-only record of a proven pre-transport failure."""
import sqlite3
import time
import unittest

import ledger


class NotSentAttemptTest(unittest.TestCase):
    def setUp(self):
        self.c = sqlite3.connect(':memory:')
        self.addCleanup(self.c.close)
        ledger.initialize(self.c)
        self.c.commit()
        self.c.execute('BEGIN IMMEDIATE')
        ledger.patch_budget(self.c, 'workspace', 'scope', dict(limit={'amount': '1', 'currency': 'USD'}, maxConcurrentJobs=4, allowAutomaticRetries=False), 0)
        self.reservation = ledger.command(self.c, 'workspace', 'scope', 'reserve',
            dict(money={'amount': '0.1', 'currency': 'USD'}, budget_revision=1, expires=time.time()+60, job='job'), 'job')['reservation']
        self.attempt, self.owner = ledger.claim_attempt(self.c, 'workspace', 'scope', self.reservation, 'job', 'chat-count', 'a'*64, 'b'*64)
        self.c.commit()

    def state(self):
        return self.c.execute('SELECT state FROM provider_attempts WHERE id=?', (self.attempt,)).fetchone()[0]

    def test_owner_can_record_not_sent_without_changing_reservation_or_events(self):
        self.c.execute('BEGIN IMMEDIATE')
        before = self.c.execute('SELECT state,amount,actual,refunded FROM reservations WHERE id=?', (self.reservation,)).fetchone()
        events = self.c.execute('SELECT COUNT(*) FROM ledger_events').fetchone()[0]
        ledger.finish_attempt(self.c, self.attempt, self.owner, 'not_sent')
        self.assertEqual(self.state(), 'not_sent')
        self.assertEqual(self.c.execute('SELECT state,amount,actual,refunded FROM reservations WHERE id=?', (self.reservation,)).fetchone(), before)
        self.assertEqual(self.c.execute('SELECT COUNT(*) FROM ledger_events').fetchone()[0], events)
        ledger.recover_attempt(self.c, self.attempt)
        self.assertEqual(self.state(), 'not_sent')

    def test_wrong_owner_and_nonexistent_attempt_cannot_finish(self):
        self.c.execute('BEGIN IMMEDIATE')
        second = ledger.command(self.c, 'workspace', 'scope', 'reserve',
            dict(money={'amount': '0.1', 'currency': 'USD'}, budget_revision=1, expires=time.time()+60, job='other'), 'other')['reservation']
        other, _ = ledger.claim_attempt(self.c, 'workspace', 'scope', second, 'other', 'chat-message', 'c'*64, 'd'*64)
        for identifier, owner in [(self.attempt, 'wrong-owner'), ('missing', self.owner), (other, self.owner)]:
            with self.subTest(identifier=identifier), self.assertRaises(ledger.LedgerError):
                ledger.finish_attempt(self.c, identifier, owner, 'not_sent')
        self.assertEqual(self.state(), 'sending')
        self.assertEqual(self.c.execute('SELECT state FROM provider_attempts WHERE id=?', (other,)).fetchone()[0], 'sending')

    def test_observed_and_unknown_cannot_be_reclassified(self):
        for terminal in ('observed', 'unknown'):
            with self.subTest(terminal=terminal):
                self.c.execute('BEGIN IMMEDIATE')
                ledger.finish_attempt(self.c, self.attempt, self.owner, terminal)
                with self.assertRaises(ledger.LedgerError):
                    ledger.finish_attempt(self.c, self.attempt, self.owner, 'not_sent')
                self.assertEqual(self.state(), terminal)
                self.c.rollback()

    def test_not_sent_cannot_be_replayed_or_receive_late_evidence(self):
        self.c.execute('BEGIN IMMEDIATE')
        ledger.finish_attempt(self.c, self.attempt, self.owner, 'not_sent')
        with self.assertRaises(ledger.AttemptExists):
            ledger.claim_attempt(self.c, 'workspace', 'scope', self.reservation, 'job', 'chat-count', 'a'*64, 'b'*64)
        with self.assertRaises(ledger.LedgerError):
            ledger.record_late_observation(self.c, self.attempt, self.owner, 'a'*64, {})
        self.assertEqual(self.state(), 'not_sent')

    def test_transaction_is_required_and_other_states_remain_rejected(self):
        with self.assertRaises(ledger.LedgerError):
            ledger.finish_attempt(self.c, self.attempt, self.owner, 'not_sent')
        self.c.execute('BEGIN IMMEDIATE')
        with self.assertRaises(ledger.LedgerError):
            ledger.finish_attempt(self.c, self.attempt, self.owner, 'invented')
        self.assertEqual(self.state(), 'sending')


if __name__ == '__main__':
    unittest.main()
