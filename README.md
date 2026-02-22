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

## Notes

- All scripts auto-detect the latest complete iteration if `--iter` is not specified
- Incomplete iterations trigger a warning but will still plot available data
- Output filenames are auto-generated with descriptive suffixes (e.g., `west_log_prob_pcoord_iter100.png`)
- For running simulations, work with a copy of `west.h5` to avoid file locking issues
