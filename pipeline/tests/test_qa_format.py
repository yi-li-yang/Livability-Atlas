import pytest

from atlas.qa.format import number, share


@pytest.mark.parametrize(
    ("value", "text"),
    [
        (0, "0.00"),
        (0.0649, "0.06"),
        (0.74, "0.74"),
        (9.994, "9.99"),
        (14.64, "14.6"),
        (99.96, "100.0"),
        (123.4, "123"),
        (6101.69, "6,102"),
        (53700.0, "53,700"),
        (-5.5, "-5.50"),
        (-1234.5, "-1,234"),
    ],
)
def test_a_number_has_a_few_significant_digits(value, text):
    assert number(value) == text


@pytest.mark.parametrize(
    ("value", "text"),
    [
        (0.0, "0%"),
        (-0.1, "0%"),
        (0.0004, "<0.1%"),
        (0.617, "61.7%"),
        (0.8414, "84.1%"),
        (0.9995, ">99.9%"),
        (1.0, "100%"),
        (1.2, "100%"),
    ],
)
def test_a_share_never_rounds_to_all_or_to_none_unless_it_is(value, text):
    assert share(value) == text
