"""SQLite journal admission, with synthetic metadata and no provider calls."""
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from chat_runtime import UsageJournal


class LegacyUsageJournalTest(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.path=Path(self.temp.name)/'live.sqlite3'
        self.journal=UsageJournal(self.path)

    def reserve(self,identifier,journal=None):
        (journal or self.journal).reserve(identifier,'synthetic-hash',identifier,100,1000)

    def test_ambiguous_sent_states_block_after_restart_without_changing_evidence(self):
        for state,metadata in [('unknown',{}),('blocked_or_unknown',{}),('outcome_unknown',{'messages_submitted':True}),
                               ('response_validation_failed',{'messages_submitted':True}),('message_started',{}),
                               ('response_received',{}),('unrecognized',{})]:
            with self.subTest(state=state),tempfile.TemporaryDirectory() as folder:
                journal=UsageJournal(Path(folder)/'trial.sqlite3');self.reserve('first',journal)
                journal.update('first',state,metadata)
                with closing(sqlite3.connect(journal.path)) as c:before=c.execute('SELECT * FROM trials').fetchall()
                restarted=UsageJournal(journal.path)
                with self.assertRaisesRegex(ValueError,'unresolved message'):self.reserve('different-turn',restarted)
                with closing(sqlite3.connect(journal.path)) as c:self.assertEqual(c.execute('SELECT * FROM trials').fetchall(),before)

    def test_existing_parallel_pre_send_reservations_and_resolved_cost_are_preserved(self):
        self.reserve('first');self.journal.update('first','count_started',{})
        self.reserve('second');self.journal.update('first','message_started',{'messages_submitted':True})
        with self.assertRaisesRegex(ValueError,'unresolved message'):self.reserve('third')
        with closing(sqlite3.connect(self.path)) as c:self.assertEqual(c.execute('SELECT count(*) FROM trials').fetchone()[0],2)
        self.journal.update('first','response_validation_failed',{},actual=45)
        self.reserve('third')
        self.journal.update('second','message_started',{'messages_submitted':True})
        with closing(sqlite3.connect(self.path)) as c:
            self.assertEqual(c.execute('SELECT state FROM trials WHERE id=?',('second',)).fetchone()[0],'message_started')

    def test_prior_reservation_cannot_start_after_another_message_becomes_unknown(self):
        self.reserve('first');self.reserve('second')
        self.journal.update('first','outcome_unknown',{'messages_submitted':True})
        with self.assertRaisesRegex(ValueError,'unresolved message'):
            self.journal.update('second','message_started',{'messages_submitted':True})
        with closing(sqlite3.connect(self.path)) as c:
            rows=c.execute('SELECT id,state,held_micro,actual_micro FROM trials ORDER BY id').fetchall()
        self.assertEqual(rows,[('first','outcome_unknown',100,None),('second','reserved',100,None)])
        self.journal.update('second','blocked_before_message',{'messages_submitted':False},release=True)
        with closing(sqlite3.connect(self.path)) as c:
            self.assertEqual(c.execute('SELECT held_micro FROM trials WHERE id=?',('second',)).fetchone()[0],0)

    def test_unknown_attempt_cannot_be_reclaimed_as_its_own_exception(self):
        self.reserve('first');self.journal.update('first','outcome_unknown',{'messages_submitted':True})
        with self.assertRaisesRegex(ValueError,'already submitted'):
            self.journal.update('first','message_started',{'messages_submitted':True})
        with closing(sqlite3.connect(self.path)) as c:
            self.assertEqual(c.execute('SELECT state,held_micro,actual_micro FROM trials').fetchone(),('outcome_unknown',100,None))

    def test_explicit_non_submission_release_and_isolated_fixture_journal(self):
        self.reserve('cancelled');self.journal.update('cancelled','blocked_before_message',{'messages_submitted':False},release=True)
        self.reserve('live-next');self.journal.update('live-next','outcome_unknown',{'messages_submitted':True})
        with self.assertRaises(ValueError):self.reserve('live-after-unknown')
        fixture=UsageJournal(Path(self.temp.name)/'fixture.sqlite3','contract-fake')
        self.reserve('fake-first',fixture);fixture.update('fake-first','outcome_unknown',{'messages_submitted':True})
        self.reserve('fake-second',fixture)

    def test_contradictory_or_malformed_submission_marker_does_not_allow_a_new_live_reservation(self):
        for marker in (True,None,'false'):
            with self.subTest(marker=marker),tempfile.TemporaryDirectory() as folder:
                journal=UsageJournal(Path(folder)/'trial.sqlite3');self.reserve('first',journal)
                journal.update('first','count_started',{'messages_submitted':marker})
                with self.assertRaises(ValueError):self.reserve('second',journal)
