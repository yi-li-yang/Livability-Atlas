# Start with a few essentials

Status: approved by the owner on 2026-11-23, in plan mode (D14). Built on branch `feat/start-with-essentials`.

## The question

The owner asked whether a user should add factors one by one, or start with all of them and remove some. Then the owner decided: no question to the user at the start, but by default only a few important factors count, "for example rent, tube, safety". The user adds the rest.

## Why not everything at the start

- **The scores bunch.** On bundle `36eb7eb8e423`, with all 15 top-level factors counted, the middle 80% of the hex cells scored between 52 and 69, a band of 17 points, against an average of 39 points for one factor alone (standard deviation 6.0 against 14.5). The factors are almost unrelated to each other (mean correlation 0.04), so each one added pulls every cell towards the middle. This is the cause of the yellow wash that D24 found.
- **What people start with, they keep.** People who start from everything keep more of it than they would choose (Park, Jun and MacInnis, 2000; repeated by Levin and others, 2002). People seldom think of removing things (Adams and others, Nature, 2021). A default reads as advice (Jachimowicz and others, 2019, a meta-analysis; disputed by Maier and others, 2022).
- **But the list must stay in sight.** People who list what matters from memory miss about half of what they later call important (Bond, Carlson and Keeney, 2008). So every other factor stays visible under "Not counted", one action from counting.

No study compares the two starts in a place finder, so this is a judgement from nearby evidence. Real tools split: SpareRoom's London wizard asks for 2 to 5 of 42 qualities; AARP and the OECD's Better Life Index start with everything on.

## The essentials

Each counts at weight 3, so each of the five top-level factors is a fifth of the score.

| Top-level factor | What counts inside it |
| --- | --- |
| Housing and cost | Renting cost |
| Transport | Walk to the nearest station; Travel time to places (the region's default places until the user adds their own, so that adding a place changes the map as it does now) |
| Safety | All of it: the crime rates and road collisions |
| Environment | Walk to a green space |
| Daily amenities | Groceries |

They are the owner's examples (rent, a station, safety), with one plain measure from each factor that most of D14's five sources weigh and that every household needs. Education and Health care are left out: whether they matter depends on the household, they are one action away, and the presets count them.

## How it works

- **The catalogue** marks each essential with `starts_counted: true`. A choice cannot start counted, since it counts once picked (D18).
- **The build** gives each factor of the bundle a `start_weight` where it differs from `default_weight`: 0 on the top factor of each branch that holds no essential. Inside such a branch every factor keeps its default, so that counting the branch's top brings all of it back. A bundle that holds no essential counts everything at the start.
- **The app** weighs a factor the profile does not set at its start weight. `default_weight` keeps its meaning: the weight a factor takes when the user counts it (D14's equal 3).
- **"Count"** in the "Not counted" list counts a factor at its default weight, with what is inside it at its start weights. A choice picked inside it keeps counting.
- **"Start from"** lists two starts before the catalogue's presets:
  - "A few essentials", the start itself, named with its essentials.
  - "Everything, equally", every factor at its default weight, as before.
- **"Reset to defaults"** returns to the essentials.
- **The presets** set what they name, on top of the essentials.
- **Saved profiles and old links keep their meaning.** The profile's text now starts with `v=2`. Text without it is from before, when every factor counted, so it is read as counting everything (`everything` in the profile, written `s=all`). "Everything, equally" uses the same marker.

## Checks

- **The build:** a bundle with renting cost, buying cost, burglary and cafés counts only renting cost inside Housing and cost, all of Safety, and starts Daily amenities at 0. A bundle with no essential counts everything.
- **The app:**
  - a factor's weight is its start weight until set, and its default weight where the profile counts everything;
  - "Count" brings back a whole branch, and keeps a picked choice counting;
  - the two starts head "Start from", and "A few essentials" is recognised where nothing is set;
  - old text and old saved profiles count everything.
- **In the browser:** a new visitor sees "A few essentials", a map with a wider spread than everything counted, and the rest of the factors under "Not counted".
