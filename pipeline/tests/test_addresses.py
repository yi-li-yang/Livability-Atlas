from atlas.datasets.countries.gb.addresses import address_key


def test_the_same_address_in_a_different_order_and_punctuation_has_the_same_key():
    a = address_key("W1F 9AA", "FLAT 3", "PETTIFOR COURT, 101", "BRADGATE ROAD")
    b = address_key("w1f9aa", "Flat 3, Pettifor Court, 101 Bradgate Road")
    assert a == b


def test_abbreviations_are_spelt_out_in_both():
    assert address_key("W1F 9AA", "12", "BROAD STREET") == address_key("W1F 9AA", "12, Broad St.")


def test_the_word_flat_is_dropped_but_the_number_is_not():
    assert address_key("W1F 9AA", "Flat 3", "12 Broad Street") == address_key(
        "W1F 9AA", "3, 12 Broad Street"
    )
    assert address_key("W1F 9AA", "Flat 3", "12 Broad Street") != address_key(
        "W1F 9AA", "Flat 4", "12 Broad Street"
    )


def test_a_different_postcode_or_house_gives_a_different_key():
    base = address_key("W1F 9AA", "12 Broad Street")
    assert base != address_key("W1F 9AB", "12 Broad Street")
    assert base != address_key("W1F 9AA", "14 Broad Street")


def test_a_missing_line_is_ignored_and_the_key_holds_no_address_text():
    key = address_key("W1F 9AA", "12 Broad Street", float("nan"), None)
    assert key == address_key("W1F 9AA", "12 Broad Street")
    assert "BROAD" not in key.upper() and len(key) == 20
