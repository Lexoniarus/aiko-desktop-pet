# Delivery history

These completed or superseded records preserve implementation decisions,
commit-specific test results and earlier review evidence. They are not current
plans, acceptance blockers or authority for runtime behavior. Original pending
checks, proposals and push/merge restrictions describe their recorded revisions.

Start with the [current documentation](../README.md),
[architecture](../ARCHITECTURE.md), [World rules](../WORLD_OBJECT_CONTRACTS.md) and
[accepted desktop smoke guide](../WORLD_SMOKE_TEST.md). Maintainer-reported
desktop acceptance was recorded on 2026-10-18; do not reinterpret old unchecked
matrices as new unfinished work or claim every historical matrix was signed off.

## Architecture and initial World delivery

- [Pet domain/UI refactor](PET_ARCHITECTURE_REFACTOR.md) and its
  [Windows checklist](PET_REFACTOR_WINDOWS_SMOKE.md): PR #9 history; it is merged.
- [Initial World implementation](WORLD_OBJECT_IMPLEMENTATION_PLAN.md).
- [OOP refactor](OOP_REFACTOR_PLAN.md) and
  [focused World follow-up](OOP_WORLD_FOLLOWUP_PLAN.md).
- [World/dialogue review](WORLD_DIALOGUE_CLEANUP_REVIEW.md).

## Perception, knowledge and search iterations

- [Persistent memory](OBJECT_MEMORY_IMPLEMENTATION_PLAN.md).
- [Offers and placement](OBJECT_PLACEMENT_AND_SEARCH_PLAN.md).
- [Committed attention](OBJECT_FOCUS_CORRECTION_PLAN.md).
- [Observed continuity](OBJECT_CONTINUITY_CORRECTION_PLAN.md).
- [Perception correction](OBJECT_PERCEPTION_CORRECTION_PLAN.md).
- [Search lifecycle](OBJECT_SEARCH_LIFECYCLE_PLAN.md) and
  [shared search](OBJECT_SEARCH_SIMPLIFICATION_PLAN.md).
- [Attention/perception simplification](ATTENTION_PERCEPTION_SIMPLIFICATION_PLAN.md).
- [Shared focus](SHARED_INTERACTION_FOCUS_PLAN.md).
- [Learned-place orientation and continuity](OBJECT_ORIENTATION_AND_CONTINUITY_PLAN.md).
- [Behavior ownership cleanup](OBJECT_BEHAVIOR_CLEANUP_PLAN.md).

## Interaction and test cleanup

- [Hover, buttons and busy feedback](OBJECT_INTERACTION_AVAILABILITY_PLAN.md).
- [Scoped interaction cleanup](OBJECT_INTERACTION_CLEANUP_PLAN.md).
- [Broader test-layer cleanup](TEST_LAYER_CLEANUP_PLAN.md).
- [Final test ownership cleanup and acceptance](TEST_OWNERSHIP_FOLLOWUP_PLAN.md).

## Social optimization follow-ups

- [B2 subjective object reunion and natural German phrases](OBJECT_RECOGNITION_DIALOGUE_FIX_PLAN.md):
  delivered as `4757da7` and `b984078`; 1,203 tests, static checks and isolated
  native real-timer playback passed. Later friendship/sleep stages remain in
  the [active care/social plan](../CARE_TIME_IMPLEMENTATION_PLAN.md).

## Pre-consolidation snapshots

These snapshots retain the replaced text so conflicting old assumptions remain
auditable without being presented as current rules:

- [Earlier World contracts](WORLD_OBJECT_CONTRACTS.md).
- [Accumulated practical checklists](WORLD_SMOKE_TEST.md).
- [Patchwork unreleased changelog](CHANGELOG_PRE_CONSOLIDATION.md).

Local links were rebased during archival. All preserved validation numbers
belong to their original baselines. Current guidance and the new-commit CI state
take precedence over old plans and green runs.
