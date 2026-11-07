"""The reasoning-as-text lesson's challenge, hidden grader. The task is small and the code is
easy; what fails is in the record (record.json): turns whose reasoning the serving stack returned
as <think> text, fed back to the model as things it said."""

import pytest

from calc import add, div, mul, sub


def test_the_four_operations():
    assert add(2, 3) == 5
    assert sub(2, 3) == -1
    assert mul(4, 3) == 12
    assert div(8, 2) == 4


def test_division_by_zero_is_a_value_error():
    with pytest.raises(ValueError):
        div(1, 0)
