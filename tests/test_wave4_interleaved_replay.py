import unittest
from deep_tests.contract_model import Command, IdempotencyConflict, ReferenceStore, generate_valid_trace, replay


class Wave4InterleavedReplayTests(unittest.TestCase):
    def test_duplicate_result_survives_interleaved_writes(self):
        store = ReferenceStore()
        stable = Command("create", "stable", "v1", "stable-create")
        first = store.apply(stable)
        for index in range(32):
            store.apply(Command("create", f"other-{index}", f"v-{index}", f"other-{index}"))
            self.assertEqual(store.apply(stable), first)
        self.assertEqual(store.revision, 33)
        self.assertEqual(len(store.history), 33)

    def test_idempotency_key_conflicts_after_many_unrelated_writes(self):
        store = ReferenceStore()
        store.apply(Command("create", "stable", "v1", "stable-key"))
        for index in range(48):
            store.apply(Command("create", f"noise-{index}", "x", f"noise-{index}"))
        with self.assertRaises(IdempotencyConflict):
            store.apply(Command("update", "stable", "v2", "stable-key"))

    def test_1200_step_trace_converges_under_prime_duplicate_schedules(self):
        commands = generate_valid_trace(20260914, steps=1200)
        snapshots = {replay(commands, duplicate_every=n).snapshot() for n in (3, 7, 19, 37)}
        self.assertEqual(len(snapshots), 1)


if __name__ == "__main__":
    unittest.main()
