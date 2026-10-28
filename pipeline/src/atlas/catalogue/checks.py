"""Catalogue rules that span several records.

models.py checks each factor and dataset alone. This module checks what only
shows across them: unique ids, scales inherited down the tree, weight reasons,
and the dataset ids that measured indicators name. Each check returns a list
of problems, each naming the factor or dataset it concerns.
"""

from atlas.catalogue.models import SCALES, DatasetsFile, Factor, FactorsFile

# 3 is the engineering default. A top-level factor always gives its reason (D14),
# and any other default weight must give its reason too.
DEFAULT_WEIGHT = 3


def check_datasets(datasets: DatasetsFile) -> list[str]:
    problems: list[str] = []
    seen: set[str] = set()
    for dataset in datasets.datasets:
        if dataset.id in seen:
            problems.append(f"dataset {dataset.id}: this id is used more than once.")
        seen.add(dataset.id)
    return problems


def check_factors(factors: FactorsFile, datasets: DatasetsFile) -> list[str]:
    known = {dataset.id: dataset for dataset in datasets.datasets}
    problems: list[str] = []
    seen: set[str] = set()

    def walk(node: Factor, parent_scales: list[str] | None) -> None:
        top_level = parent_scales is None
        if node.id in seen:
            problems.append(f"{node.id}: this id is used more than once.")
        seen.add(node.id)

        if top_level and node.weight_reason is None:
            problems.append(f"{node.id}: a top-level factor needs a weight_reason (D14).")
        elif node.default_weight != DEFAULT_WEIGHT and node.weight_reason is None:
            problems.append(
                f"{node.id}: a default_weight other than {DEFAULT_WEIGHT} needs a weight_reason."
            )

        scales = parent_scales or list(SCALES)
        if node.scales is None:
            if top_level:
                problems.append(f"{node.id}: a top-level factor must list its scales.")
        elif parent_scales is not None and not set(node.scales) <= set(parent_scales):
            problems.append(f"{node.id}: it lists a scale that its parent does not have.")
        else:
            scales = list(node.scales)

        if node.children is not None:
            for child in node.children:
                walk(child, scales)
            return

        listed = node.datasets or []
        for index, dataset_id in enumerate(listed):
            if dataset_id in listed[:index]:
                problems.append(f"{node.id}: dataset {dataset_id} is listed twice.")
            elif dataset_id not in known:
                problems.append(f"{node.id}: datasets.yaml has no dataset {dataset_id}.")
            elif node.evidence_type == "ranking" and known[dataset_id].credibility is None:
                problems.append(
                    f"{node.id}: evidence type ranking needs a credibility rating "
                    f"on dataset {dataset_id}."
                )

    for factor in factors.factors:
        walk(factor, None)
    return problems
