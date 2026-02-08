import pytest

from bcp.domain.block_types import BlockTypeOnly, UnknownBlockTypeError, BlockType


def test_all_canonical_block_types_are_accepted():
    for t in BlockType:
        b = BlockTypeOnly.create(t.value)
        assert b.block_type == t


def test_unknown_block_type_fails_loudly_with_clear_error():
    with pytest.raises(UnknownBlockTypeError) as excinfo:
        BlockTypeOnly.create("HOLIDAY")

    msg = str(excinfo.value)
    assert "HOLIDAY" in msg
    assert "Allowed types" in msg
    # Ensure we are not silently coercing or allowing free-text
    assert "RECORDING_WINDOW" in msg
