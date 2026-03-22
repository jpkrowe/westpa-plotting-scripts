# WESTPA Analysis Scripts

A collection of reusable scripts for analyzing WESTPA weighted ensemble simulations.

## Requirements

- Python 3.7+
- numpy
- matplotlib
- h5py

## Scripts

### plot_prob_pcoord.py

Plot probability distributions vs progress coordinate as histograms (1D) or heatmaps (2D).

```bash
# 1D histogram (default: log scale, dimension 0)
plot_prob_pcoord.py west.h5

# Specific iteration
plot_prob_pcoord.py west.h5 --iter 100

# Linear scale
plot_prob_pcoord.py west.h5 --linear

# Different dimension
plot_prob_pcoord.py west.h5 --dims 1

# 2D heatmap
plot_prob_pcoord.py west.h5 --dims 0 1

# Custom bins and output
plot_prob_pcoord.py west.h5 --dims 0 1 --bins 100 --output heatmap.png
```

| Option | Description |
|--------|-------------|
| `--iter, -i` | Iteration number (default: latest complete) |
| `--output, -o` | Output file path (default: auto-generated) |
| `--bins, -b` | Number of histogram bins (default: 50) |
| `--linear, -l` | Use linear scale instead of log |
| `--dims, -d` | Pcoord dimension(s): one for 1D, two for 2D heatmap |

---

### scatter_prob_pcoord.py

Scatter plot of individual trajectories. In 1D mode, plots pcoord vs weight. In 2D mode, plots two pcoord dimensions with color representing weight.

```bash
# 1D scatter: pcoord vs weight
scatter_prob_pcoord.py west.h5

# Specific iteration
scatter_prob_pcoord.py west.h5 --iter 100

# 2D scatter: dim 0 vs dim 1, colored by weight
scatter_prob_pcoord.py west.h5 --dims 0 1

# Linear scale
scatter_prob_pcoord.py west.h5 --linear
```

| Option | Description |
|--------|-------------|
| `--iter, -i` | Iteration number (default: latest complete) |
| `--output, -o` | Output file path (default: auto-generated) |
| `--linear, -l` | Use linear scale instead of log |
| `--dims, -d` | Pcoord dimension(s): one for 1D, two for 2D |

---

### plot_extrema_pcoord.py

Plot the minimum or maximum progress coordinate value at each iteration as a line plot. Useful for tracking how far the ensemble has explored along a coordinate over the course of a simulation.

```bash
# Min pcoord (dim 0) across all iterations (default)
plot_extrema_pcoord.py west.h5

# Max pcoord instead
plot_extrema_pcoord.py west.h5 --mode max

# Track a different dimension
plot_extrema_pcoord.py west.h5 --dims 1

# Restrict to an iteration range
plot_extrema_pcoord.py west.h5 --first-iter 10 --last-iter 200

# Custom output
plot_extrema_pcoord.py west.h5 --mode max --output max_pcoord.png
```

| Option | Description |
|--------|-------------|
| `--mode, -m` | `min` or `max` (default: `min`) |
| `--dims, -d` | Pcoord dimension to track (default: 0) |
| `--first-iter` | First iteration to include (default: first available) |
| `--last-iter` | Last iteration to include (default: latest complete) |
| `--output, -o` | Output file path (default: auto-generated) |

---

## Notes

- All scripts auto-detect the latest complete iteration if `--iter` is not specified
- Incomplete iterations trigger a warning but will still plot available data
- Output filenames are auto-generated with descriptive suffixes (e.g., `west_log_prob_pcoord_iter100.png`)
- For running simulations, work with a copy of `west.h5` to avoid file locking issues
