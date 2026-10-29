# User-choice indicators

Status: built in two pull requests. [D18](../decisions.md#d18-preference-types) gives each measured indicator a preference type. The first three types (fixed, user direction, user range) need one column in the bundle. A **user choice** indicator needs one column for each option the user can pick: a faith, an ethnic group.

## Which indicators

- **Your community:** the share of residents in a group, from Census 2021 by output area. The options are the census's detailed ethnic groups, its religions, the places of birth it gives at the smallest areas, and life stages made from its age bands. Main language is not offered, because the census gives the detailed languages only down to boroughs.
- **Faith:** the walking minutes to the nearest place of worship of a religion, from OpenStreetMap. The options are the religions with enough places in the region.
- Cuisines (D19) will use it too.

## The bundle

- A choice indicator has `options` in the manifest: a list of `{id, name, group, column}`. `column` holds the prefix of the option columns, which are named `<prefix>__<option id>` in `cells.parquet`. An indicator has either `options` or a plain column, never both.
- Every option has one column of raw values and is scored by the indicator's curve (a percentile curve ranks each option's column on its own).
- `group` titles a section of the picker ("Ethnic group", "Religion").
- The pipeline writes only the options it can measure: a religion with fewer than 10 places in the region is left out.

## The score

- The profile gains `choices`: for each choice indicator, the ids of the options picked. With none picked, the indicator has no score and the factors around it carry on without it.
- With several picked, a cell scores the best of them: the highest score among the picked options. A person who picks two faiths wants a place of either nearby; a person who picks two ethnic groups wants either present. This keeps the score a weighted sum of one score per indicator that anyone can follow.
- The direction of a choice indicator is fixed, and the interface offers no "flip". Composition is framed as the presence of a group the user chooses, never as fewer of a group (D08).
- Weight: a choice factor starts at 0 (D18). The first time the user picks an option, the factor's weight becomes 3, the middle of the scale. Clearing the last option puts it back to 0.

## Privacy (D08)

Choices are sensitive: an ethnic group or a religion. They stay in the browser's storage. They are **not** written into the link's fragment, unlike the weights, because a shared link would then say who the sender is. A person who opens a shared link keeps their own choices.

## The picker

On the factor panel, an indicator with options shows a "Choose" button in place of the direction switch. It opens a list of checkboxes under the group titles. The indicator is "not counted" until the first pick, as at weight 0.

## Explaining a score

"Why this score" shows the best picked option for the cell, with its value and score, so the user sees which choice carried it.
