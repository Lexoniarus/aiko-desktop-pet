"""Generated wishes and real completion policies, without injected rewards."""

import unittest

from tools.care_balance_scenarios import CareScenario


class GeneratedCareBalanceTests(unittest.TestCase):
    def test_four_daily_visits_and_intensive_refreshes_have_distinct_outcomes(self):
        average = CareScenario(friendship=70, intensive=False, seed=7)
        intensive = CareScenario(friendship=90, intensive=True, seed=7)
        ordinary_days, intensive_days = average.run(3), intensive.run(3)
        self.assertTrue(all(4 <= row["successes"] <= 12 for row in ordinary_days))
        self.assertTrue(all(24 <= row["successes"] <= 48 for row in intensive_days))
        self.assertTrue(60 <= average.pet.friendship < 80)
        self.assertGreaterEqual(intensive.pet.friendship, 90)
        self.assertGreater(intensive.completed, average.completed * 2)
        self.assertEqual((average.rounds, intensive.rounds), (24, 96))
        self.assertEqual((average.social, intensive.social), (24, 60))
        self.assertFalse(average.pet.friendship_history.rewards)
        self.assertFalse(intensive.pet.friendship_history.rewards)
        self.assertEqual(average.pet.lived_seconds, 3 * 86400)
        self.assertEqual(intensive.pet.lived_seconds, 3 * 86400)

    def test_average_visits_do_not_maintain_initial_level_ten(self):
        ordinary = CareScenario(friendship=90, intensive=False, seed=7)
        ordinary.run(1)
        self.assertLess(ordinary.pet.friendship, 90)


if __name__ == "__main__":
    unittest.main()
