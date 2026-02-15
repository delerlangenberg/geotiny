#!/usr/bin/env python3
"""
Quick visualization of seismic data.

Generates plots of seismograms and spectrograms for analysis.
"""

import argparse
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


def plot_csv_data(csv_file, output_dir=None):
    """Plot seismic data from CSV file."""
    import pandas as pd
    
    try:
        # Read CSV
        df = pd.read_csv(csv_file, parse_dates=['timestamp'])
        
        # Get channel columns (exclude timestamp)
        channels = [col for col in df.columns if col != 'timestamp']
        
        # Create figure with subplots
        fig, axes = plt.subplots(len(channels), 1, figsize=(12, 3*len(channels)))
        if len(channels) == 1:
            axes = [axes]
        
        fig.suptitle(f'Seismogram: {csv_file.stem}', fontsize=14, fontweight='bold')
        
        # Plot each channel
        for ax, channel in zip(axes, channels):
            ax.plot(df['timestamp'], df[channel], linewidth=0.5)
            ax.set_ylabel(f'{channel}\n(counts)', fontsize=10)
            ax.grid(True, alpha=0.3)
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
        
        axes[-1].set_xlabel('Time (UTC)', fontsize=10)
        plt.tight_layout()
        
        # Save or show
        if output_dir:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            output_file = output_path / f"{csv_file.stem}_plot.png"
            plt.savefig(output_file, dpi=150, bbox_inches='tight')
            print(f"✓ Saved plot to {output_file}")
        else:
            plt.show()
        
        plt.close()
        return True
        
    except Exception as e:
        print(f"✗ Error plotting {csv_file.name}: {e}")
        return False


def plot_mseed_data(mseed_file, output_dir=None):
    """Plot seismic data from miniSEED file using ObsPy."""
    try:
        from obspy import read
        
        st = read(str(mseed_file))
        
        # Create plot
        fig = st.plot(show=False, size=(1200, 800))
        
        if output_dir:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            output_file = output_path / f"{mseed_file.stem}_plot.png"
            fig.savefig(output_file, dpi=150, bbox_inches='tight')
            print(f"✓ Saved plot to {output_file}")
        else:
            plt.show()
        
        plt.close()
        return True
        
    except ImportError:
        print("ObsPy not installed. Install with: pip install obspy")
        return False
    except Exception as e:
        print(f"✗ Error plotting {mseed_file.name}: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Plot seismic data")
    parser.add_argument("input", help="Input file or directory")
    parser.add_argument("--output", help="Output directory for plots (default: show plot)")
    parser.add_argument("--format", default="csv", choices=["csv", "mseed"], help="Input format")
    args = parser.parse_args()
    
    input_path = Path(args.input)
    
    # Process single file or directory
    if input_path.is_file():
        files = [input_path]
    else:
        files = list(input_path.glob(f"*.{args.format}"))
    
    if not files:
        print(f"No files found matching *.{args.format}")
        return
    
    print(f"Found {len(files)} file(s) to plot")
    
    success_count = 0
    for file in files:
        if args.format == "csv":
            if plot_csv_data(file, args.output):
                success_count += 1
        elif args.format == "mseed":
            if plot_mseed_data(file, args.output):
                success_count += 1
    
    print(f"\nCompleted: {success_count}/{len(files)} plots generated successfully")


if __name__ == "__main__":
    main()
