"""Care receipts keep bounded real references and independent processing cursors."""

import copy
import json
import unittest

from aiko_pet.infrastructure.care_evidence_codec import (
    decode_care_evidence,
    encode_care_evidence,
)
from aiko_pet.pet.care_evidence import (
    MAX_CARE_EXPERIENCES,
    CareActivity,
    CareEncounter,
    CareEvidenceState,
    CareExperience,
    LongTermProgress,
)
from aiko_pet.pet.moodlets import MoodletId, MoodletOutcome
from aiko_pet.pet.wishes import WishArea, WishTargetKind


class CareEvidenceCodecTests(unittest.TestCase):
    def test_bounded_receipts_preserve_links_and_reject_false_timelines(self):
        state = CareEvidenceState(
            0,
            2,
            (CareEncounter(1, 100, 120),),
            (
                CareExperience(
                    "round:a:1",
                    120,
                    CareActivity.PLAY,
                    MoodletOutcome.WIN,
                    WishArea.GAMES,
                    WishTargetKind.GAME,
                    "mastermind",
                    1,
                    pleasant=True,
                ),
            ),
            (
                LongTermProgress(MoodletId.TRUSTING, 86400, 86400, 90000),
                LongTermProgress(MoodletId.APPRECIATED, 0, 0, 90000),
            ),
        )
        original = json.loads(json.dumps(encode_care_evidence(state), allow_nan=False))
        self.assertEqual(decode_care_evidence(original, 0, 90000), state)
        for mutate in (
            lambda e: e.update(baseline=90001),
            lambda e: e.update(next_encounter_id=1),
            lambda e: e["experiences"][0].update(encounter_id=9),
            lambda e: e["experiences"][0].update(occurred_at=121),
            lambda e: e.update(experiences=e["experiences"] * 2),
            lambda e: e["experiences"][0].update(pleasant=1),
            lambda e: e["experiences"][0].update(boundary_violated=True),
            lambda e: e["progress"][0].update(definition_id="pride"),
            lambda e: e["progress"][0].update(processed_until=86401),
            lambda e: e["progress"][0].update(awake_contact_gap_seconds=float("nan")),
            lambda e: e["progress"][1].update(definition_id="trusting"),
            lambda e: e.update(
                experiences=e["experiences"] * (MAX_CARE_EXPERIENCES + 1),
            ),
        ):
            raw = copy.deepcopy(original)
            mutate(raw)
            with self.assertRaises(ValueError):
                decode_care_evidence(raw, 0, 90000)
