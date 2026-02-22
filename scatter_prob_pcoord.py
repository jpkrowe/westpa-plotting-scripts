#!/usr/bin/env python3
"""
Scatter plot of trajectories for a WESTPA weighted ensemble simulation.

Each point represents a trajectory/segment. In 2D mode, points are colored by weight.

Usage:
    scatter_prob_pcoord.py <west.h5> [--iter N] [--output FILE] [--linear]
    scatter_prob_pcoord.py <west.h5> --dims 0 1 [--iter N] [--linear]
"""

import argparse
import sys
import h5py
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm


def get_latest_complete_iteration(h5file):
    """Find the latest iteration where all segments are complete."""
    iterations = h5file['iterations']
    iter_nums = sorted([int(k.replace('iter_', '')) for k in iterations.keys()])

    for iter_num in reversed(iter_nums):
        iter_grp = iterations[f'iter_{iter_num:08d}']
        if 'seg_index' not in iter_grp:
            continue
        seg_index = iter_grp['seg_index'][:]
        status = seg_index['status']
        # Status 2 = SEG_STATUS_COMPLETE
        if np.all(status == 2):
            return iter_num
    return None


def plot_scatter_1d(ax, pcoord_vals, weights, log_scale, dim_label):
    """Create 1D scatter plot with weight on y-axis."""
    if log_scale:
        ax.scatter(pcoord_vals, weights, alpha=0.6, c='steelblue', edgecolors='black', linewidths=0.5)
        ax.set_yscale('log')
        ylabel = 'log(Weight)'
    else:
        ax.scatter(pcoord_vals, weights, alpha=0.6, c='steelblue', edgecolors='black', linewidths=0.5)
        ylabel = 'Weight'

    ax.set_xlabel(f'Progress Coordinate (dim {dim_label})', fontsize=12)
    ax.set_ylabel(ylabel, fontsize=12)
    ax.grid(True, alpha=0.3)


def plot_scatter_2d(ax, pcoord_x, pcoord_y, weights, log_scale, dim_labels):
    """Create 2D scatter plot with color representing weight."""
    if log_scale:
        # Use log scale for colors
        nonzero_mask = weights > 0
        vmin = weights[nonzero_mask].min() if nonzero_mask.any() else 1e-20
        vmax = weights.max()
        norm = LogNorm(vmin=vmin, vmax=vmax)
        sc = ax.scatter(pcoord_x, pcoord_y, c=weights, cmap='viridis', norm=norm,
                        alpha=0.7, edgecolors='black', linewidths=0.3)
        cbar_label = 'log(Weight)'
    else:
        sc = ax.scatter(pcoord_x, pcoord_y, c=weights, cmap='viridis',
                        alpha=0.7, edgecolors='black', linewidths=0.3)
        cbar_label = 'Weight'

    plt.colorbar(sc, ax=ax, label=cbar_label)
    ax.set_xlabel(f'Progress Coordinate (dim {dim_labels[0]})', fontsize=12)
    ax.set_ylabel(f'Progress Coordinate (dim {dim_labels[1]})', fontsize=12)
    ax.grid(True, alpha=0.3)


def scatter_prob_pcoord(h5_path, iteration=None, output=None, log_scale=True, dims=None):
    """
    Scatter plot of trajectories for a given iteration.

    Parameters
    ----------
    h5_path : str
        Path to the west.h5 file
    iteration : int, optional
        Iteration number. If None, uses latest complete iteration.
    output : str, optional
        Output file path. If None, auto-generates based on input file and iteration.
    log_scale : bool
        Use log scale for weight axis/colorbar (default: True)
    dims : list of int, optional
        Dimension indices to plot. If None or single value, creates 1D plot.
        If two values, creates 2D scatter with color = weight.
    """
    with h5py.File(h5_path, 'r') as f:
        # Determine iteration to use
        if iteration is None:
            iteration = get_latest_complete_iteration(f)
            if iteration is None:
                print("Error: No complete iterations found!", file=sys.stderr)
                sys.exit(1)
            print(f"Using latest complete iteration: {iteration}")

        # Check iteration exists
        iter_key = f'iter_{iteration:08d}'
        if iter_key not in f['iterations']:
            print(f"Error: Iteration {iteration} not found!", file=sys.stderr)
            sys.exit(1)

        iter_grp = f['iterations'][iter_key]
        seg_index = iter_grp['seg_index'][:]
        pcoord = iter_grp['pcoord'][:]  # shape: (n_segs, n_timepoints, n_dims)

        # Check completion status
        status = seg_index['status']
        n_complete = np.sum(status == 2)
        n_total = len(status)

        if n_complete != n_total:
            print(f"Warning: Iteration {iteration} is incomplete ({n_complete}/{n_total} segments)",
                  file=sys.stderr)

        weights = seg_index['weight']
        n_pcoord_dims = pcoord.shape[2]

        print(f"Iteration: {iteration}")
        print(f"Segments: {n_total} ({n_complete} complete)")
        print(f"Pcoord dimensions: {n_pcoord_dims}")
        print(f"Weight range: {weights.min():.2e} to {weights.max():.2e}")

        # Determine plotting mode
        if dims is None:
            dims = [0]

        # Validate dimensions
        for d in dims:
            if d >= n_pcoord_dims:
                print(f"Error: Dimension {d} requested but pcoord only has {n_pcoord_dims} dimensions",
                      file=sys.stderr)
                sys.exit(1)

        is_2d = len(dims) == 2

        # Extract pcoord values (last timepoint)
        if is_2d:
            pcoord_x = pcoord[:, -1, dims[0]]
            pcoord_y = pcoord[:, -1, dims[1]]
            print(f"Pcoord dim {dims[0]} range: {pcoord_x.min():.4f} to {pcoord_x.max():.4f}")
            print(f"Pcoord dim {dims[1]} range: {pcoord_y.min():.4f} to {pcoord_y.max():.4f}")
        else:
            pcoord_vals = pcoord[:, -1, dims[0]]
            print(f"Pcoord dim {dims[0]} range: {pcoord_vals.min():.4f} to {pcoord_vals.max():.4f}")

    # Create plot
    fig, ax = plt.subplots(figsize=(10, 8) if is_2d else (10, 6))

    if is_2d:
        plot_scatter_2d(ax, pcoord_x, pcoord_y, weights, log_scale, dims)
        ax.set_title(f'Trajectory Scatter Plot\nIteration {iteration} ({n_total} segments)', fontsize=14)
        dim_str = f"_dims{dims[0]}{dims[1]}"
    else:
        plot_scatter_1d(ax, pcoord_vals, weights, log_scale, dims[0])
        ax.set_title(f'Trajectory Scatter Plot\nIteration {iteration} ({n_total} segments)', fontsize=14)
        dim_str = f"_dim{dims[0]}" if dims[0] != 0 else ""

    plt.tight_layout()

    # Determine output path
    if output is None:
        base = h5_path.rsplit('.h5', 1)[0]
        scale_str = 'log_' if log_scale else ''
        output = f"{base}_{scale_str}scatter{dim_str}_iter{iteration}.png"

    plt.savefig(output, dpi=150)
    print(f"\nPlot saved to: {output}")

    return output


def main():
    parser = argparse.ArgumentParser(
        description='Scatter plot of trajectories for WESTPA simulations',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # 1D scatter: pcoord vs weight
    %(prog)s west.h5

    # Plot specific iteration
    %(prog)s west.h5 --iter 100

    # Plot with linear scale
    %(prog)s west.h5 --linear

    # Plot a different pcoord dimension
    %(prog)s west.h5 --dims 1

    # 2D scatter: dim 0 vs dim 1, colored by weight
    %(prog)s west.h5 --dims 0 1

    # 2D scatter with custom output
    %(prog)s west.h5 --dims 0 1 --output scatter.png
"""
    )

    parser.add_argument('h5_file', help='Path to west.h5 file')
    parser.add_argument('--iter', '-i', type=int, default=None,
                        help='Iteration number (default: latest complete)')
    parser.add_argument('--output', '-o', type=str, default=None,
                        help='Output file path (default: auto-generated)')
    parser.add_argument('--linear', '-l', action='store_true',
                        help='Use linear scale instead of log scale')
    parser.add_argument('--dims', '-d', type=int, nargs='+', default=None,
                        help='Pcoord dimension(s) to plot. One value for 1D, two for 2D (default: 0)')

    args = parser.parse_args()

    # Validate dims
    if args.dims is not None and len(args.dims) > 2:
        print("Error: --dims accepts at most 2 dimensions", file=sys.stderr)
        sys.exit(1)

    scatter_prob_pcoord(
        h5_path=args.h5_file,
        iteration=args.iter,
        output=args.output,
        log_scale=not args.linear,
        dims=args.dims
    )


if __name__ == '__main__':
    main()
