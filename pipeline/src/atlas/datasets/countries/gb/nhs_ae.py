"""Hospitals with an A&E department, from the NHS website's "Find your nearest A&E" (dataset
`nhs-find-an-ae`). NHS website content is released under the Open Government Licence v3.0.

NHS England publishes no list of emergency departments by site, but the NHS website's service
search lists them, with the NHS organisation code, the address and the opening hours. A search
from a postcode returns about 50 departments, nearest first, so a few searches from places across
a region list every department in and around it. The sites are kept after the first fetch.
"""

import html
import re
import time
from pathlib import Path

import pandas as pd
import requests

URL = "https://www.nhs.uk/service-search/find-an-accident-and-emergency-service/results?location={}"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; LivabilityAtlas; +https://github.com/yi-li-yang/Livability-Atlas)"
}
PAUSE = 1.0  # seconds between searches
POSTCODE = re.compile(r"[A-Z]{1,2}\d[A-Z\d]? ?\d[A-Z]{2}")
ALL_DAY = "Open 24 hours"  # NHS England's definition of a type 1 department: open 24 hours


def _page(postcode: str) -> str:
    reply = requests.get(URL.format(postcode.replace(" ", "%20")), headers=HEADERS, timeout=60)
    reply.raise_for_status()
    return reply.text


def _text(fragment: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", fragment))).strip()


def parse_results(page: str) -> list[dict[str, str]]:
    """The departments listed on a results page, each with its NHS organisation `code`, `name`,
    `address`, `postcode` (empty where the address has none) and opening `hours`."""
    found = []
    for item in re.split(r'<li id="result_item_\d+"', page)[1:]:
        code = re.search(r'id="item_id_\d+"[^>]*>([^<]+)<', item)
        name = re.search(r'id="orgname_\d+"[^>]*>(.*?)</h3>', item, flags=re.S)
        hours = re.search(r'id="opening_times_list_\d+_\d+"[^>]*>(.*?)</ul>', item, flags=re.S)
        address = re.search(r'id="address_\d+"[^>]*>(.*?)</p>', item, flags=re.S)
        if not (code and name and address):
            continue
        text = _text(address.group(1))
        postcode = POSTCODE.search(text.upper())
        found.append(
            {
                "code": code.group(1).strip(),
                "name": _text(name.group(1)),
                "address": text,
                "postcode": postcode.group(0) if postcode else "",
                "hours": _text(hours.group(1)) if hours else "",
            }
        )
    return found


def fetch(data_dir: Path, region_id: str, seeds: list[str]) -> Path:
    """Searches from each of the `seeds` (postcodes) and keeps the departments found, once each,
    in `data/raw/nhs-ae/sites-<region>.csv`. A search is made once: delete the file for new
    sites."""
    target = data_dir / "raw" / "nhs-ae" / f"sites-{region_id}.csv"
    if target.exists():
        return target
    sites: dict[str, dict[str, str]] = {}
    for seed in seeds:
        time.sleep(PAUSE)
        for found in parse_results(_page(seed)):
            sites.setdefault(found["code"], found)
    target.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        list(sites.values()), columns=["code", "name", "address", "postcode", "hours"]
    ).to_csv(target.with_name(target.name + ".part"), index=False, encoding="utf-8")
    target.with_name(target.name + ".part").replace(target)
    return target


def read_sites(path: Path) -> pd.DataFrame:
    """The departments open 24 hours that have a postcode, with `code`, `name` and `Postcode`."""
    sites = pd.read_csv(path, encoding="utf-8", keep_default_na=False)
    kept = sites.loc[(sites["hours"] == ALL_DAY) & (sites["postcode"] != "")]
    return kept.rename(columns={"postcode": "Postcode"})[["code", "name", "Postcode"]].reset_index(
        drop=True
    )
