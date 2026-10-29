"""Checks a written bundle, writes its QA report beside it, and publishes it unless a check failed.

Publishing is moving `latest.json`, which the web app follows. A bundle that fails stays on disk
with its report, so that the report can be read, and is not published.
"""

from pathlib import Path

from atlas.catalogue.load import Catalogue
from atlas.publish.bundle import previous_version, publish_latest, published_version
from atlas.qa.regional import Regional
from atlas.qa.report import Report, check_bundle, write_report


def check(bundle: Path, catalogue: Catalogue, *, regional: Regional | None = None) -> Report:
    """Checks a written bundle against the one that publishing it would replace, and writes the
    report beside it. It does not publish."""
    region_dir = bundle.parent
    replaced = previous_version(region_dir, bundle.name)
    report = check_bundle(
        bundle,
        catalogue,
        previous=region_dir / replaced if replaced is not None else None,
        published=published_version(region_dir) == bundle.name,
        regional=regional,
    )
    write_report(bundle, report)
    return report


def release(bundle: Path, catalogue: Catalogue, *, regional: Regional | None = None) -> Report:
    """Checks a written bundle, and publishes it if no check failed."""
    report = check(bundle, catalogue, regional=regional)
    if not report.failed:
        publish_latest(bundle.parent, bundle.name)
    return report
