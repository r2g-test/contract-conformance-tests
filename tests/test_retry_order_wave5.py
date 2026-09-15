import unittest

from deep_tests.contract_model import (
    Command,
    IdempotencyConflict,
    ReferenceStore,
    generate_valid_trace,
    replay,
)


class RetryOrderWave5Tests(unittest.TestCase):
    def test_original_create_key_stays_bound_after_delete_and_recreate(self):
        store = ReferenceStore()
        store.apply(Command("create", "alpha", "v1", "create-alpha-original"))
        store.apply(Command("delete", "alpha", None, "delete-alpha-v1"))
        store.apply(Command("create", "alpha", "v2", "create-alpha-v2"))

        with self.assertRaises(IdempotencyConflict):
            store.apply(Command("create", "alpha", "different", "create-alpha-original"))

        self.assertEqual(store.revision, 3)
        self.assertIn('"alpha":"v2"', store.snapshot())

    def test_delayed_duplicate_delete_is_stable_after_64_writes_and_reincarnation(self):
        store = ReferenceStore()
        store.apply(Command("create", "alpha", "v1", "create-alpha-v1"))
        deleted = store.apply(Command("delete", "alpha", None, "delete-alpha-v1"))
        for index in range(64):
            store.apply(Command("create", f"other-{index}", f"value-{index}", f"create-other-{index}"))
        store.apply(Command("create", "alpha", "v2", "create-alpha-v2"))

        revision_before_retry = store.revision
        history_before_retry = store.history
        self.assertEqual(
            deleted,
            store.apply(Command("delete", "alpha", None, "delete-alpha-v1")),
        )
        self.assertEqual(store.revision, revision_before_retry)
        self.assertEqual(store.history, history_before_retry)
        self.assertIn('"alpha":"v2"', store.snapshot())

    def test_2400_step_trace_converges_under_sparse_prime_duplicate_schedules(self):
        commands = generate_valid_trace(20260915, steps=2400)
        schedules = (2, 5, 13, 31, 61)
        snapshots = {replay(commands, duplicate_every=n).snapshot() for n in schedules}
        self.assertEqual(len(snapshots), 1)


if __name__ == "__main__":
    unittest.main()
