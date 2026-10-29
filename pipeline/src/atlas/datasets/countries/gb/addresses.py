"""How an address is matched across two registers, with no address kept.

HM Land Registry writes a sale's address in parts (a house number or name, a flat, a street) and
the energy performance register in three free lines, in a different order and with different
abbreviations. Both are reduced to the same fingerprint: the postcode without its space, and the
sorted words of the address, with the common abbreviations spelt out and the words "flat" and
"apartment" dropped. The fingerprint is a hash, so a table of fingerprints holds no address.
Both registers' address fields come from Ordnance Survey and Royal Mail: see the `licence_note`
of the energy performance certificates.
"""

import hashlib
import re

# Words that mean the same in the two registers, and words that add nothing to an address.
SYNONYMS = {
    "ST": "STREET", "RD": "ROAD", "AVE": "AVENUE", "LN": "LANE", "CT": "COURT", "DR": "DRIVE",
    "GDNS": "GARDENS", "PL": "PLACE", "SQ": "SQUARE", "CRES": "CRESCENT", "TER": "TERRACE",
    "GRN": "GREEN", "PK": "PARK", "HSE": "HOUSE", "APARTMENT": "", "FLAT": "", "UNIT": "",
}  # fmt: skip


def address_key(postcode: object, *lines: object) -> str:
    """The fingerprint of an address given as a postcode and any lines in any order."""
    text = re.sub(
        r"[^A-Z0-9]+",
        " ",
        " ".join(str(line) for line in lines if line is not None and line == line).upper(),
    )
    words = sorted(w for w in (SYNONYMS.get(w, w) for w in text.split()) if w)
    squashed = re.sub(r"\s+", "", str(postcode).upper())
    return hashlib.sha256(f"{squashed}|{' '.join(words)}".encode()).hexdigest()[:20]
