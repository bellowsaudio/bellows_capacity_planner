# tests/domain/test_block_collisions.py

from datetime import date

import pytest

from bcp.domain.blocks import Block, BlockOverlapError, BlockStore


def test_overlap_internal_corrections_with_away_fails():
    store = BlockStore()
    store.add(Block.create("AWAY_FROM_STUDIO", date(2026, 1, 10), date(2026, 1, 12)))

    with pytest.raises(BlockOverlapError) as exc:
        store.add(Block.create("INTERNAL_CORRECTIONS", date(2026, 1, 12), date(2026, 1, 12)))

    assert "Illegal overlap" in str(exc.value)
    assert "INTERNAL_CORRECTIONS" in str(exc.value)
    assert "AWAY_FROM_STUDIO" in str(exc.value)


def test_overlap_publisher_corrections_with_away_fails():
    store = BlockStore()
    store.add(Block.create("AWAY_FROM_STUDIO", date(2026, 2, 1), date(2026, 2, 1)))

    with pytest.raises(BlockOverlapError):
        store.add(Block.create("PUBLISHER_CORRECTIONS_WINDOW", date(2026, 2, 1), date(2026, 2, 2)))


def test_overlap_recording_window_with_away_is_allowed():
    """
    AWAY days must be able to exist inside a recording window;
    later math subtracts them from recordable days.
    """
    store = BlockStore()
    store.add(Block.create("RECORDING_WINDOW", date(2026, 3, 1), date(2026, 3, 31)))

    # Overlaps but should be allowed
    store.add(Block.create("AWAY_FROM_STUDIO", date(2026, 3, 10), date(2026, 3, 12)))

    assert len(store.all_blocks()) == 2
