#!/usr/bin/env python3
"""
Convert seismic data files to CSV format for easy analysis.

Supports multiple input formats including miniSEED, SAC, and others
supported by ObsPy.
"""

import argparse
from pathlib import Path
import pandas as pd


def convert_mseed_to_csv(input_file, output_file):
    """Convert miniSEED file to CSV using ObsPy."""
    try:
        from obspy import read
        
        # Read the seismic data
        st = read(str(input_file))
        
        # Create a DataFrame from all traces
        data_frames = []
        for tr in st:
            df = pd.DataFrame({
                'timestamp': pd.date_range(
                    start=tr.stats.starttime.datetime,
                    periods=tr.stats.npts,
                    freq=f'{1/tr.stats.sampling_rate}S'
                ),
                f'{tr.stats.channel}': tr.data
            })
            data_frames.append(df)
        
        # Merge all channels
        if data_frames:
            result = data_frames[0]
            for df in data_frames[1:]:
                result = result.merge(df, on='timestamp', how='outer')
            
            # Save to CSV
            result.to_csv(output_file, index=False)
            print(f"✓ Converted {input_file.name} -> {output_file.name}")
            return True
    
    except ImportError:
        print("ObsPy not installed. Install with: pip install obspy")
        return False
    except Exception as e:
        print(f"✗ Error converting {input_file.name}: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Convert seismic data to CSV")
    parser.add_argument("input", help="Input file or directory")
    parser.add_argument("--output", help="Output directory (default: data/processed/)")
    parser.add_argument("--format", default="mseed", help="Input format (default: mseed)")
    args = parser.parse_args()
    
    input_path = Path(args.input)
    output_dir = Path(args.output) if args.output else Path("data/processed")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Process single file or directory
    if input_path.is_file():
        files = [input_path]
    else:
        files = list(input_path.glob(f"*.{args.format}"))
    
    if not files:
        print(f"No files found matching *.{args.format}")
        return
    
    print(f"Found {len(files)} file(s) to convert")
    
    success_count = 0
    for file in files:
        output_file = output_dir / f"{file.stem}.csv"
        if convert_mseed_to_csv(file, output_file):
            success_count += 1
    
    print(f"\nCompleted: {success_count}/{len(files)} files converted successfully")


if __name__ == "__main__":
    main()
