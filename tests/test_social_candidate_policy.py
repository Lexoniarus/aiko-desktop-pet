"""Candidate intervals preserve admissions and category-specific exclusions."""

import unittest

from aiko_pet.application.social_candidates import (
    JOKE_FILTER_REVISION,
    MAX_JOKE_ID,
    JokeCandidatePolicy,
    JokeCatalog,
    JokeExclusion,
)
from aiko_pet.pet.social_content_evidence import SocialCategory


class CandidatePolicyTests(unittest.TestCase):
    def test_overlapping_exclusions_and_admitted_ids_leave_disjoint_ranges(self):
        category = SocialCategory.SINGLE
        exclusions = (
            JokeExclusion(category, 2, 4, "length", 200),
            JokeExclusion(category, 3, 6, "no_match", 200),
            JokeExclusion(category, 8, 8, "format", 200),
        )
        ranges = JokeCandidatePolicy.remaining_ranges(
            JokeCatalog(0, 10, 200), category,
            ("jokeapi:0", "jokeapi:10", "zitat-service:1"), exclusions, 100,
        )
        self.assertEqual(ranges, ((1, 1), (7, 7), (9, 9)))

    def test_expired_foreign_category_and_old_filter_exclusions_are_ignored(self):
        category = SocialCategory.SINGLE
        exclusions = (
            JokeExclusion(category, 0, 1, "length", 100),
            JokeExclusion(SocialCategory.TWO_PARTS, 2, 3, "no_match", 200),
            JokeExclusion(category, 4, 5, "format", 200,
                          revision=JOKE_FILTER_REVISION + 1),
        )
        self.assertEqual(JokeCandidatePolicy.remaining_ranges(
            JokeCatalog(0, 5, 200), category, (), exclusions, 100,
        ), ((0, 5),))

    def test_exhaustion_does_not_relax_admitted_identity_history(self):
        self.assertEqual(JokeCandidatePolicy.remaining_ranges(
            JokeCatalog(4, 5, 200), SocialCategory.TWO_PARTS,
            ("jokeapi:4", "jokeapi:5"), (), 100,
        ), ())

    def test_out_of_bounds_and_large_exclusions_are_clipped_to_catalog(self):
        category = SocialCategory.SINGLE
        exclusions = (
            JokeExclusion(category, 0, 20, "no_match", 200),
            JokeExclusion(category, 50, MAX_JOKE_ID, "no_match", 200),
        )
        self.assertEqual(JokeCandidatePolicy.remaining_ranges(
            JokeCatalog(10, 60, 200), category, (), exclusions, 100,
        ), ((21, 49),))
