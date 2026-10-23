# Livability Atlas
A decision tool for answering one question: **where should I live?**

## The Big Idea
Choosing a place to live is one of the largest decisions a person makes, yet it is usually made with generic rankings, anecdotes, and gut feeling. This project builds a tool that treats the question seriously: it combines many kinds of evidence about a place, weighs them according to my own priorities.

The question appears at two scales, and the project covers both:

1. **Within a city.** Which neighbourhoods suit me best, light up the map where I should find my home.
2. **Across countries and cities.** Where should I base myself for a stay abroad, retirement, work, or study?

These are the same problem at different zoom levels: many factors, personal weights, and a decision that deserves more rigour than a listicle. Different data sources can/should be leveraged.

## Motivation

- I need a tool to customize the selection/filter for the living conditions.
- I need to figure out the most comprehensive factors that contributes to life quality: price, community, transport, pollution, air and water quality, green space, education, climate, development... every aspect that matters, and I want to adjust their weight. 
- I want to use it to explore different regions in the world, or in my residency country.
- For a specific city, I want to search for the best location to live.


## Product Goals

**Primary goal.** Score map by the condition of the weighted factors and give suggestions. 

## How to develop

- Start with a minimal viable product, but consider its scalability when select the tech stack. It can grow really big, eventually it could be a APP and has external users.
- First find and list all kinds of living quality factors, this need to be very comprehensive.
- Then think about which ones can be quantified, are there existing data set, API, or we need to build tools for it, start with easy ones, then add from the most important, and the easiest to add.
- Then develop the user interface and consider scalablity.
- and define cycles of development.

- This is a project developing with ClaudeCode and VSCode.
- Use markdown files to track progress, record decisions, map the project directory when it grows to thousands of files.
- Design the development framework really well from the beginning, 
- think about other important things i haven't covered
