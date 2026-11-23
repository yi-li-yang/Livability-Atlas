# Interface

Status: planned (D17, accepted). The factor explorer in step 0.2 of Phase 0 prototypes the visual factor tree.

## Progressive disclosure

The surface shows what a decision needs. Each further layer opens only when the user asks, and every layer is one action away from the layer above it.

| Layer | What the user sees | How they get there |
| --- | --- | --- |
| 1. Map | Hex cells coloured by livability score; a short legend; the top neighbourhoods by name and score | The default view |
| 2. Quick look | Neighbourhood name, score and rank, its two biggest strengths and its biggest weakness (e.g. "+ Transport, + Green space, − Cost") | Hover over or tap a hex cell |
| 3. Why this score | One bar per top-level factor, showing its score contribution | Click the hex cell |
| 4. Inside a factor | That factor's sub-factor scores | Open the factor's dropdown |
| 5. Evidence | Raw value and unit, scoring curve, dataset, date, licence and evidence type | The "details" link on a measured indicator |

The same rule applies across the app:

- The preferences panel shows top-level factors, and sub-factors open in dropdowns.
- Inside a dropdown, subjective factors show a "more ↔ less" switch or an ideal-range slider, and choice factors show a picker.
- Scoring curves and data-coverage settings sit behind "Advanced".
- Dataset credits sit behind "About the data".
- The legend shows where the region's scores lie: a small bar for each twentieth of the scale above the colour bar, ticks at 0, 50 and 100, and a line such as "Most of London scores 50 to 70". A switch beside its title, "Score" and "Rank in London", colours the map by the score or by the fifth of the region each cell falls in (D24), kept in the browser. While the map shows the livability score, it marks the top neighbourhoods' best cells with their places in the list, over the place names. On a phone the spread line, the marks' key, the switch and "Colour strength" are behind "Colours". Each key is a small hexagon drawn as the map draws the cells it names; with hard limits, the legend adds the grey they leave and how many hex cells, such as "Left out by your hard limits: 8,900 of 12,300".
- The legend's "Show on the map" list colours the map by one factor's or one measured indicator's own score in place of the livability score ([spec](specs/2026-10-29-map-by-factor.md)). The ranking, the top neighbourhoods and the hard limits stay as they are, and the quick look and the reasons add the score on the map beside the livability score.
- **Start from** above the factor tree lists the two starts and then the presets (D14). "A few essentials" is where a new user starts: only the essentials count, and every other factor is under "Not counted". "Everything, equally" counts every factor at its default weight. The presets are ready-made preference profiles that the manifest carries (`catalogue/presets/`, cut to the factors of the bundle), set on top of the essentials. Choosing one sets the weights, directions and hard limits; the choices, bands and the way the factors combine stay the user's. While the profile is still the preset's, the list names it with its description and an "Undo" back to what the user had before.
- **How the factors combine** under the factor tree is a switch between "Add up" (the default) and "No weak spots" (scoring.md, section 5). It goes in the link as `m=balanced`. In "No weak spots" the reasons show each factor's own score ("72 out of 100") in place of points, with a line that says why they do not add up.
- **Your places**, above the hard limits, holds up to 3 places the user travels to often ([spec](specs/2026-11-22-own-places.md)). Each has a name the user types and is added by a postcode or by "Choose on the map", then clicking a cell. With one place or more, travel time scores the time to them in place of the default places; the map marks each place, and the reasons list the minutes to each, as an estimate. Places stay in the browser's storage, never in the link, and a postcode is looked up in a table the app loads, so it is sent nowhere.
- **Top neighbourhoods**, once open, says how many of them stay when a weight moves by a fifth ("9 of these 10 stay, on average, …", the stability of the top, scoring.md section 12a) and marks with ● those that stay whichever weight moves. It is worked out only while the list is open, once the weights have been still for 0.3 s, one scenario at a time, so the page keeps responding.
- On a phone (under 768 px wide), panels become bottom sheets ([spec](specs/2026-10-29-phone-layout.md)): the preferences are a bar along the bottom that opens, the legend moves across the top, tapping a cell opens the reasons as a short peek (the score, the rank, the strengths and weakness) with "Show the reasons" for the rest, so the cell tapped stays in sight above it, and there is no quick look, since a phone has no hover.
- The map keeps clear of the panels over it (the preferences, the legend, the reasons, a sheet): it opens with the region's centre in the middle of the part they leave clear, a neighbourhood chosen from the list lands there, and a cell chosen under the reasons moves out from under them (the critique of the map, 2026-11-23).

## Visual factor tree

The preferences panel draws the factor tree, and each factor's area is its share of the total weight.

- **Resizing.** Moving a weight slider resizes that factor at once, and the others shrink or grow to match. This is exactly how weights act in the score.
- **Drill-down.** Clicking a factor zooms into its sub-factors, which resize the same way. "Back" returns to the level above.
- **Weight 0.** A factor at weight 0 leaves the drawing and moves to a short "not counted" list, where "Count" brings it in at its default weight. At the start, every factor but the essentials is there (D14). Opened, such a factor says that nothing in it changes the map until it counts, with a "Count" button. "Start again" goes back to the start.
- **Layout.** A treemap (nested rectangles) or a sunburst (rings around a centre), with a switch between them. The treemap shows first (D17). The app calls them "Boxes" and "Rings", the switch sits beside the heading, and the choice is kept in the browser and not in the link, since it is how the user likes to see the factors and not what they want.
- **The rings.** An inner ring of the factors at this level, each as wide as its share of the weight, with the counted sub-factors of each in a lighter ring outside it, sharing its angle. The centre names the level. Pointing at an arc names it and gives its share, clicking an arc opens the factor (an outer arc opens its factor and the sub-factor inside it), and clicking the centre goes up a level. The sliders beside the drawing stay the way to set a weight, and the way to use a keyboard.
- **Colour.** Each factor has its own colour, from the categorical palette of the Salt design system. Its sub-factors take a tint of it. The weights panel shows each colour beside its factor's name, so it doubles as the legend, and labels name every shape, so colour is never the only cue.

## Controls inside a factor

| Control | For | Example |
| --- | --- | --- |
| Weight slider, 0–5 | Every factor | |
| "More is better" and "Less is better" switch | Measured indicators of preference type "user direction". It sits under the indicator's weight slider, and which one starts pressed is the catalogue's direction | Rain, nightlife nearby |
| Ideal-range band: "Full marks from … to …", with a "From" and a "To" slider between the region's lowest and highest values | Preference type "user range" | Summer temperature, building age |
| Picker | Preference type "user choice" | Industry, cuisines, community group, faith |
| Hard limit | Any measured indicator with a must-have threshold. They are set in their own "Hard limits" section under the factor tree: choose a measure, then at most or at least a number, or the categories allowed. A hex cell that fails one turns a light grey, which keeps the map readable, and is not ranked | Rent no higher than a cap |

## Plain and accessible

- Labels use only the words in the glossary's [In the app](glossary.md#in-the-app) part, which carry no jargon.
- Colours stay readable for colour-blind users.
- Every score has one colour scale: red is worse, yellow middling, blue-green better. The map, the legend, the bars of "Why this score" and the chip beside "On the map" all use it, so a factor named for a bad thing, such as Crime, reads as good or bad at a glance. The good end leans to blue so that the ends stay apart in colour blindness; the bars also give the score as a length and a number.
- A hex cell with few or no homes, such as a park, an airport or an industrial estate, has no score (D22). The map leaves it clear with a thin outline that grows with the zoom (too thin to see over all of London, a pixel or two close up), so the basemap shows what is there: parks and woods in a pale grey-green, industrial and business land in a pale lilac, railways in a pale stone. The legend says "Few or no homes: no score", beside a key in those colours. The quick look and the reasons say why, and give no rank.
- The colours sit under the water, roads, railways and place names (D23), so the map's lines and names stay sharp, and the colours are nearly solid (80%, which "Colour strength" changes).
- Everything works with a keyboard.
- The ranked list is a full alternative to the map for screen-reader users.
