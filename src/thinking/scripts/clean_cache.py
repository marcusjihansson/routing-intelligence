#!/usr/bin/env python3
"""Cache cleaning script for DSPy and related ML caches.

This script provides safe, automated cache cleaning with dry-run mode,
selective cleaning options, and safety checks to prevent data loss.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


def get_cache_sizes() -> Dict[str, Tuple[str, int]]:
    """Analyze cache sizes across all known cache directories.

    Returns:
        Dict mapping cache names to (path, size_in_bytes)
    """
    home = Path.home()
    cache_dir = home / ".cache"

    cache_info = {
        "dspy": (str(cache_dir / "model_requests_cache"), 0),
        "huggingface": (str(cache_dir / "huggingface"), 0),
        "uv": (str(cache_dir / "uv"), 0),
        "pip": (str(cache_dir / "pip"), 0),
        "deepdoctection": (str(cache_dir / "deepdoctection"), 0),
        "doctr": (str(cache_dir / "doctr"), 0),
        "selenium": (str(cache_dir / "selenium"), 0),
    }

    for name, (path, _) in cache_info.items():
        if Path(path).exists():
            size = get_directory_size(path)
            cache_info[name] = (path, size)
        else:
            cache_info[name] = (path, 0)

    return cache_info


def get_directory_size(path: str) -> int:
    """Calculate directory size in bytes.

    Args:
        path: Directory path to calculate size for

    Returns:
        Size in bytes (0 if path doesn't exist or can't be accessed)
    """
    try:
        return sum(f.stat().st_size for f in Path(path).rglob("*") if f.is_file())
    except (PermissionError, FileNotFoundError):
        return 0


def get_disk_space() -> Tuple[int, int, int]:
    """Get current disk space information.

    Returns:
        (total_gb, used_gb, available_gb)
    """
    try:
        result = subprocess.run(
            ["df", "-h", "/System/Volumes/Data"],
            capture_output=True,
            text=True,
            check=True,
        )
        lines = result.stdout.strip().split("\n")
        if len(lines) >= 2:
            parts = lines[1].split()
            total = parse_size(parts[1])
            used = parse_size(parts[2])
            available = parse_size(parts[3])
            return (total, used, available)
    except (subprocess.CalledProcessError, IndexError, ValueError):
        pass
    return (0, 0, 0)


def parse_size(size_str: str) -> int:
    """Parse size string to GB.

    Args:
        size_str: Size string like "191Gi" or "40Gi"

    Returns:
        Size in GB (as integer)
    """
    size_str = size_str.upper()
    if size_str.endswith("TI") or size_str.endswith("T"):
        return int(float(size_str[:-1]) * 1024)
    elif size_str.endswith("GI") or size_str.endswith("G"):
        return int(float(size_str[:-1]))
    elif size_str.endswith("MI") or size_str.endswith("M"):
        return int(float(size_str[:-1]) / 1024)
    return 0


def format_size(bytes_size: int) -> str:
    """Format bytes to human-readable string.

    Args:
        bytes_size: Size in bytes

    Returns:
        Formatted string like "24G" or "105M"
    """
    for unit in ["B", "K", "M", "G", "T"]:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f}{unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f}P"


def safe_remove_cache(
    cache_name: str,
    cache_path: str,
    dry_run: bool = True,
    force: bool = False,
    verbose: bool = True,
) -> bool:
    """Safely remove cache directory.

    Args:
        cache_name: Name of cache for logging
        cache_path: Path to cache directory
        dry_run: If True, only print what would be done
        force: If True, remove without confirmation
        verbose: If True, print detailed messages

    Returns:
        True if removed (or would be removed), False otherwise
    """
    path = Path(cache_path)

    if not path.exists():
        if verbose:
            print(f"  ✗ {cache_name}: Path doesn't exist: {cache_path}")
        return False

    if dry_run:
        if verbose:
            print(f"  ✓ {cache_name}: Would remove {cache_path}")
        return True

    if not force:
        try:
            response = input(f"Remove {cache_name} cache at {cache_path}? [y/N] ")
            if response.lower() != "y":
                print(f"  ✗ {cache_name}: Skipped")
                return False
        except (EOFError, KeyboardInterrupt):
            print(f"\n  ✗ {cache_name}: Skipped (interrupted)")
            return False

    try:
        shutil.rmtree(cache_path)
        if verbose:
            print(f"  ✓ {cache_name}: Removed {cache_path}")
        return True
    except (PermissionError, OSError) as e:
        print(f"  ✗ {cache_name}: Failed to remove - {e}")
        return False


def backup_cache(
    cache_name: str, cache_path: str, backup_dir: str, verbose: bool = True
) -> bool:
    """Backup cache directory before removal.

    Args:
        cache_name: Name of cache for logging
        cache_path: Path to cache directory
        backup_dir: Directory to backup to
        verbose: If True, print detailed messages

    Returns:
        True if backed up successfully, False otherwise
    """
    path = Path(cache_path)
    backup = Path(backup_dir)

    if not path.exists():
        if verbose:
            print(f"  ✗ {cache_name}: Path doesn't exist, nothing to backup")
        return False

    try:
        backup.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup / f"{cache_name}_{timestamp}"

        shutil.copytree(cache_path, backup_path)
        if verbose:
            print(f"  ✓ {cache_name}: Backed up to {backup_path}")
        return True
    except (PermissionError, OSError) as e:
        print(f"  ✗ {cache_name}: Backup failed - {e}")
        return False


def select_caches_to_clean(
    cache_info: Dict[str, Tuple[str, int]],
    selection: Optional[List[str]] = None,
    exclude: Optional[List[str]] = None,
) -> List[str]:
    """Select which caches to clean based on user input.

    Args:
        cache_info: Dictionary of cache information
        selection: List of cache names to include (None for all)
        exclude: List of cache names to exclude

    Returns:
        List of cache names to clean
    """
    if selection:
        selected = [name for name in selection if name in cache_info]
    else:
        selected = list(cache_info.keys())

    if exclude:
        selected = [name for name in selected if name not in exclude]

    return selected


def print_cache_analysis(cache_info: Dict[str, Tuple[str, int]]) -> None:
    """Print detailed cache size analysis.

    Args:
        cache_info: Dictionary of cache information
    """
    print("\n" + "=" * 60)
    print("CACHE ANALYSIS")
    print("=" * 60)

    total_size = 0
    for name, (path, size) in sorted(cache_info.items(), key=lambda x: -x[1][1]):
        if size > 0:
            print(f"  {name:20s} {format_size(size):>8s}  {path}")
            total_size += size

    print("-" * 60)
    print(f"  {'TOTAL':20s} {format_size(total_size):>8s}")

    total_gb, used_gb, avail_gb = get_disk_space()
    if total_gb > 0:
        print("\n" + "=" * 60)
        print("DISK SPACE (System/Volumes/Data)")
        print("=" * 60)
        print(f"  Total:     {total_gb:8.1f} GB")
        print(f"  Used:      {used_gb:8.1f} GB")
        print(f"  Available: {avail_gb:8.1f} GB ({used_gb / total_gb * 100:.0f}% used)")


def main() -> int:
    """Main entry point for cache cleaning script.

    Returns:
        Exit code (0 for success, 1 for errors)
    """
    parser = argparse.ArgumentParser(
        description="Clean ML and package manager caches to free disk space"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be cleaned without actually cleaning",
    )
    parser.add_argument(
        "--cache",
        nargs="+",
        choices=[
            "dspy",
            "huggingface",
            "uv",
            "pip",
            "deepdoctection",
            "doctr",
            "selenium",
            "all",
        ],
        help="Specific caches to clean (default: dspy, huggingface, uv, pip)",
    )
    parser.add_argument(
        "--exclude",
        nargs="+",
        choices=[
            "dspy",
            "huggingface",
            "uv",
            "pip",
            "deepdoctection",
            "doctr",
            "selenium",
        ],
        help="Caches to exclude from cleaning",
    )
    parser.add_argument(
        "--force", action="store_true", help="Clean without confirmation"
    )
    parser.add_argument(
        "--backup",
        type=str,
        metavar="DIR",
        help="Backup caches to specified directory before removal",
    )
    parser.add_argument(
        "--min-space",
        type=float,
        default=10.0,
        help="Minimum required free space in GB (default: 10.0)",
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Print detailed information"
    )

    args = parser.parse_args()

    print_cache_analysis(get_cache_sizes())

    total_gb, used_gb, avail_gb = get_disk_space()
    if avail_gb >= args.min_space and not args.dry_run:
        print(
            f"\n✓ Sufficient disk space available ({avail_gb:.1f}GB >= {args.min_space}GB)"
        )
        print("  No cleaning needed. Use --force to clean anyway.")
        return 0

    cache_info = get_cache_sizes()

    if args.cache and "all" in args.cache:
        cache_selection = list(cache_info.keys())
    elif args.cache:
        cache_selection = args.cache
    else:
        cache_selection = ["dspy", "huggingface", "uv", "pip"]

    cache_selection = select_caches_to_clean(cache_info, cache_selection, args.exclude)

    if not cache_selection:
        print("\nNo caches selected for cleaning.")
        return 0

    print("\n" + "=" * 60)
    if args.dry_run:
        print("DRY RUN - Preview of cache cleanup")
    else:
        print("CACHE CLEANUP")
    print("=" * 60)

    removed_count = 0
    total_removed = 0

    for cache_name in cache_selection:
        cache_path, size = cache_info[cache_name]

        if args.backup and not args.dry_run:
            backup_cache(cache_name, cache_path, args.backup, args.verbose)

        if safe_remove_cache(
            cache_name,
            cache_path,
            dry_run=args.dry_run,
            force=args.force,
            verbose=args.verbose,
        ):
            removed_count += 1
            total_removed += size

    if args.dry_run:
        print(
            f"\nWould remove {removed_count} cache(s) totaling {format_size(total_removed)}"
        )
    else:
        print(
            f"\nRemoved {removed_count} cache(s) totaling {format_size(total_removed)}"
        )

        new_total_gb, new_used_gb, new_avail_gb = get_disk_space()
        if new_avail_gb > avail_gb:
            freed = new_avail_gb - avail_gb
            print(f"Freed approximately {freed:.1f}GB of disk space")

    return 0


if __name__ == "__main__":
    sys.exit(main())
