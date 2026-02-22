#!/usr/bin/env python3
"""
Plot probability vs progress coordinate for a WESTPA weighted ensemble simulation.

Supports both 1D bar plots and 2D heatmaps.

Usage:
    plot_prob_pcoord.py <west.h5> [--iter N] [--output FILE] [--bins N] [--linear]
    plot_prob_pcoord.py <west.h5> --dims 0 1 [--iter N] [--bins N] [--linear]
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


def plot_prob_pcoord_1d(ax, pcoord_vals, weights, n_bins, log_scale):
    """Create 1D probability histogram."""
    bins = np.linspace(pcoord_vals.min(), pcoord_vals.max(), n_bins + 1)
    bin_centers = (bins[:-1] + bins[1:]) / 2

    prob_hist = np.zeros(n_bins)
    for pc, w in zip(pcoord_vals, weights):
        bin_idx = np.searchsorted(bins[1:], pc)
        if bin_idx < n_bins:
            prob_hist[bin_idx] += w

    if log_scale:
        nonzero_mask = prob_hist > 0
        ax.bar(bin_centers[nonzero_mask], prob_hist[nonzero_mask],
               width=(bins[1]-bins[0])*0.9, alpha=0.7, color='steelblue', edgecolor='black')
        ax.set_yscale('log')
        ylabel = 'log(Probability)'
    else:
        ax.bar(bin_centers, prob_hist,
               width=(bins[1]-bins[0])*0.9, alpha=0.7, color='steelblue', edgecolor='black')
        ylabel = 'Probability'

    ax.set_ylabel(ylabel, fontsize=12)
    ax.grid(True, alpha=0.3)

    return prob_hist


def plot_prob_pcoord_2d(ax, pcoord_x, pcoord_y, weights, n_bins, log_scale, dim_labels):
    """Create 2D probability heatmap."""
    # Create 2D histogram bins
    x_bins = np.linspace(pcoord_x.min(), pcoord_x.max(), n_bins + 1)
    y_bins = np.linspace(pcoord_y.min(), pcoord_y.max(), n_bins + 1)

    # Compute weighted 2D histogram
    prob_hist = np.zeros((n_bins, n_bins))
    for px, py, w in zip(pcoord_x, pcoord_y, weights):
        x_idx = np.searchsorted(x_bins[1:], px)
        y_idx = np.searchsorted(y_bins[1:], py)
        if x_idx < n_bins and y_idx < n_bins:
            prob_hist[y_idx, x_idx] += w

    # Set zero values to NaN for better visualization (will appear white)
    prob_hist_plot = prob_hist.copy()
    prob_hist_plot[prob_hist_plot == 0] = np.nan

    # Plot heatmap
    if log_scale:
        # Find min non-zero value for log scale
        nonzero_vals = prob_hist[prob_hist > 0]
        if len(nonzero_vals) > 0:
            vmin = nonzero_vals.min()
            vmax = nonzero_vals.max()
            norm = LogNorm(vmin=vmin, vmax=vmax)
        else:
            norm = None
        im = ax.pcolormesh(x_bins, y_bins, prob_hist_plot, cmap='viridis', norm=norm, shading='flat')
        cbar_label = 'log(Probability)'
    else:
        im = ax.pcolormesh(x_bins, y_bins, prob_hist_plot, cmap='viridis', shading='flat')
        cbar_label = 'Probability'

    # Add colorbar
    cbar = plt.colorbar(im, ax=ax, label=cbar_label)

    ax.set_xlabel(f'Progress Coordinate (dim {dim_labels[0]})', fontsize=12)
    ax.set_ylabel(f'Progress Coordinate (dim {dim_labels[1]})', fontsize=12)

    return prob_hist


def plot_prob_pcoord(h5_path, iteration=None, output=None, n_bins=50, log_scale=True, dims=None):
    """
    Plot probability vs progress coordinate for a given iteration.

    Parameters
    ----------
    h5_path : str
        Path to the west.h5 file
    iteration : int, optional
        Iteration number. If None, uses latest complete iteration.
    output : str, optional
        Output file path. If None, auto-generates based on input file and iteration.
    n_bins : int
        Number of bins for histogram (default: 50)
    log_scale : bool
        Use log scale for probability axis (default: True)
    dims : list of int, optional
        Dimension indices to plot. If None or single value, creates 1D plot.
        If two values, creates 2D heatmap.
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
        plot_prob_pcoord_2d(ax, pcoord_x, pcoord_y, weights, n_bins, log_scale, dims)
        ax.set_title(f'Probability Heatmap\nIteration {iteration}', fontsize=14)
        dim_str = f"_dims{dims[0]}{dims[1]}"
    else:
        plot_prob_pcoord_1d(ax, pcoord_vals, weights, n_bins, log_scale)
        ax.set_xlabel(f'Progress Coordinate (dim {dims[0]})', fontsize=12)
        ax.set_title(f'Probability vs Progress Coordinate\nIteration {iteration}', fontsize=14)
        dim_str = f"_dim{dims[0]}" if dims[0] != 0 else ""

    plt.tight_layout()

    # Determine output path
    if output is None:
        base = h5_path.rsplit('.h5', 1)[0]
        scale_str = 'log_' if log_scale else ''
        plot_type = 'heatmap' if is_2d else 'prob_pcoord'
        output = f"{base}_{scale_str}{plot_type}{dim_str}_iter{iteration}.png"

    plt.savefig(output, dpi=150)
    print(f"\nPlot saved to: {output}")

    return output


def main():
    parser = argparse.ArgumentParser(
        description='Plot probability vs progress coordinate for WESTPA simulations',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Plot 1D histogram of dimension 0 (default)
    %(prog)s west.h5

    # Plot specific iteration
    %(prog)s west.h5 --iter 100

    # Plot with linear scale
    %(prog)s west.h5 --linear

    # Plot a different pcoord dimension
    %(prog)s west.h5 --dims 1

    # Plot 2D heatmap of dimensions 0 and 1
    %(prog)s west.h5 --dims 0 1

    # 2D heatmap with custom bins and output
    %(prog)s west.h5 --dims 0 1 --bins 100 --output heatmap.png
"""
    )

    parser.add_argument('h5_file', help='Path to west.h5 file')
    parser.add_argument('--iter', '-i', type=int, default=None,
                        help='Iteration number (default: latest complete)')
    parser.add_argument('--output', '-o', type=str, default=None,
                        help='Output file path (default: auto-generated)')
    parser.add_argument('--bins', '-b', type=int, default=50,
                        help='Number of histogram bins (default: 50)')
    parser.add_argument('--linear', '-l', action='store_true',
                        help='Use linear scale instead of log scale')
    parser.add_argument('--dims', '-d', type=int, nargs='+', default=None,
                        help='Pcoord dimension(s) to plot. One value for 1D, two for 2D heatmap (default: 0)')

    args = parser.parse_args()

    # Validate dims
    if args.dims is not None and len(args.dims) > 2:
        print("Error: --dims accepts at most 2 dimensions", file=sys.stderr)
        sys.exit(1)

    plot_prob_pcoord(
        h5_path=args.h5_file,
        iteration=args.iter,
        output=args.output,
        n_bins=args.bins,
        log_scale=not args.linear,
        dims=args.dims
    )


if __name__ == '__main__':
    main()
