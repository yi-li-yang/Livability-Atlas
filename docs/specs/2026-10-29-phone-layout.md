# The phone layout

Status: built, in one pull request. [interface.md](../interface.md) says that on a phone the panels become bottom sheets that slide up over the map. Until now the preferences panel, 20 rem wide and as tall as the screen allowed, covered most of a phone and hid the map it is there to steer.

## The rule

Below 768 px of width (a phone, held either way) the app uses the phone layout. At or above it nothing changes. The layout is chosen in the app (`useIsPhone`, a media query that the browser reports) and not by CSS alone, because the two layouts hold different things, not the same things in other places.

## What changes

- **The preferences are a sheet along the bottom.** Closed, it is a bar that reads "What matters to you" with an arrow; the map shows above it. Opening it shows the top neighbourhoods, the factor tree and the hard limits as before, in an opaque sheet of at most two thirds of the map's height that scrolls. The sheet's own handle carries the title, so the factor tree does not repeat it. Closing it keeps what the user had opened inside it.
- **The legend moves to the top of the map**, across its width, with the "Show on the map" list and the colour bar. The cell opacity slider sits behind "Cell opacity", which opens it, since a phone has no room to spare for a control that most visits leave alone.
- **Tapping a cell opens the reasons as a sheet** from the bottom, at most 70% of the map's height and opaque, in place of the preferences, with its Close button; closing it brings the preferences back. A phone has no hover, so the quick look is not drawn there.
- **The basemap's credit stays in view above the closed sheet.** It is a licence condition (OpenStreetMap, via OpenFreeMap), so it must not sit under a panel. Where the sheet is open it covers the map's own credit, so the credit is also a line of "About the data" under the map, which no sheet covers.
- **Held sideways** (still under 768 px), the legend drops its title and label (kept for screen readers) to a select and a colour bar, and the sheets are at most half and 55% of the map's height, so that the legend and a sheet never meet.
- **Choosing a neighbourhood** from the top list shuts the sheet, so the map shows where it went.

## What does not change

Every control, the weights, the choices, the limits, the link and the storage, and the scoring. A shared link opens in either layout.

## Checks

End-to-end tests in a phone-sized window: the sheet is closed at first and the map shows; it opens and the sliders work; the legend and the sheet do not overlap; the credit is visible and clear of the sheet; tapping a cell shows the reasons across the full width, over the preferences; and there is no quick look. The desktop tests still run in their own window and pass as before.
