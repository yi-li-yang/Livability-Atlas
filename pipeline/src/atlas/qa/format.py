"""How the QA report writes numbers."""


def number(x: float) -> str:
    """A value with a few significant digits: 0.74, 14.6, 123 and 6,102."""
    size = abs(x)
    if size >= 1000:
        return f"{x:,.0f}"
    if size >= 100:
        return f"{x:.0f}"
    if size >= 10:
        return f"{x:.1f}"
    return f"{x:.2f}"


def share(x: float) -> str:
    """A share of cells as a percentage that is not 0% or 100% unless it is exactly that."""
    if x <= 0:
        return "0%"
    if x >= 1:
        return "100%"
    percent = x * 100
    if percent < 0.1:
        return "<0.1%"
    if percent > 99.9:
        return ">99.9%"
    return f"{percent:.1f}%"
