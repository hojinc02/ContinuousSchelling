# Continuous Schelling Model
This repository contains an algorithm for simulating a Schelling Model in a continuous two-dimensional space, incorporating population count restrictions for each subsection of the map. It also includes an interactive HoloViews plot with dynamic zoom functionality to visualize population movement over time.

### Schelling Simulation with San Diego County's Population Data
![sd_gif](sd_gif.gif)

## Algorithm
Each subsection $$i$$ of the map starts with an initial population count $$P_i$$. A percentage threshold $$S$$ defines the maximum allowable population as $$P_i(1+S)$$. During each iteration, residents act in random order: each checks the ratio $$$F$$ of similar neighbors within a radius $$r$$ to the total number of neighbors. If $$F \lt L$$, where $$L$$ is the tolerance threshold, the resident relocates to a random vacant subsection of the map and chooses a random location within it. If $$ F \geq L $$, the resident remains in place.
