# The map by one factor

Status: built. The roadmap's "Layers of detail" milestone lists a single-factor view, such as crime only. [interface.md](../interface.md) says what the map shows by default: the livability score.

## What it is

A user can colour the map by one factor's own score, or by one measured indicator's, in place of the livability score. It answers "where is crime lowest?" and "where is transport best?" without changing the weights.

## The control

"Show on the map" is a list in the legend, above the colour bar, since that is where the user reads what the colours mean. It starts on "Livability score". It lists every factor and measured indicator of the manifest's tree, grouped by top-level factor and indented by depth, so a factor added to the catalogue appears in it with no change to the app's code. A choice indicator (a faith, a group) is left out, because it has no score until the user picks an option, and so is a factor that holds nothing else.

## The score

The score of a factor is the weighted mean of the scores of the children inside it that have data, by the weights inside it, from 0 to 100, exactly as the livability score is the weighted mean of the top-level factors. A factor's own weight does not matter, since it is not weighed against its siblings. A measured indicator's score is its curve's score. A cell with no data inside it has no score and is drawn as a cell with no score. If everything inside the factor is at weight 0, the map has no data, and the legend says so.

`scoreRegion` takes the id of the node and is checked against the one-cell engine (`scoreCell`), the same reference as the livability score.

## What a view does not change

The ranking, the top neighbourhoods and the hard limits answer "where should I live?", which is the livability score, so a view must not change the answer. A cell that a hard limit leaves out is still greyed and not ranked. The quick look and the reasons keep the livability score and its rank, and add a line "On the map: Safety, 40 out of 100", with the livability score labelled, so the number and the colour are never mistaken for each other.

## Not kept

The choice is what the user is looking at, not what they want, so it is not in the link or the browser's storage: the map starts on the livability score at each visit.

## Decisions to review

- The list sits in the legend and not on each factor's row, so the rows stay as they are and the control is next to the colours it changes.
- The top neighbourhoods stay by livability score. Ranking them by the factor on the map would be a second, separate feature.
