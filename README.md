# Continuous Schelling Model
This repository contains an algorithm for simulating a Schelling Model in a continuous two-dimensional space, incorporating population count restrictions for each subsection of the map. It also includes an interactive HoloViews plot with dynamic zoom functionality to visualize population movement over time.

### Schelling Simulation with San Diego County's Population Data
![sd_gif](sd_gif.gif)

## Algorithm
Each subsection $$i$$ of the given map has an initial population count $$P_i$$. A percentage threshold $$S$$ determines the maximum possible population count $$P_i \cdot (1+S)$$. For every iteration, in a random order, each resident checks the number of similar neighbors in a radius $$r$$, and if the ratio $$F$$ of similar neighbor count to total neighbor count is $$F \lt L$$ where $$L$$ is a tolerance threshold, the resident picks a random vacant subsection of the map and relocates to a random location within the chosen subsection, and does not relocate if $$F \geq L$$. 
