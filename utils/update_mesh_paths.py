#!/usr/bin/env python3

import sys
import xml.etree.ElementTree as ET
from pathlib import Path
import argparse
import shutil
import re

def update_mesh_paths(urdf_path: Path, new_prefix: str, dry_run: bool = False) -> None:
    """Update mesh paths in URDF file."""
    print("\n=== Updating Mesh Paths ===")

    # Parse URDF
    tree = ET.parse(urdf_path)
    root = tree.getroot()

    # Track changes
    changes = 0
    old_paths = set()
    new_paths = set()

    # Find all mesh elements
    for mesh in root.findall(".//mesh"):
        filename = mesh.get('filename')
        if filename:
            # Store old path
            old_paths.add(filename)

            # Extract just the filename part
            match = re.search(r'[^/]+\.STL$', filename)
            if match:
                mesh_filename = match.group(0)
                new_filename = f"{new_prefix}/{mesh_filename}"

                # Store new path
                new_paths.add(new_filename)

                if not dry_run:
                    mesh.set('filename', new_filename)
                changes += 1

    # Print summary
    print("\nPath changes:")
    for old, new in zip(sorted(old_paths), sorted(new_paths)):
        print(f"{old} -> {new}")

    if not dry_run:
        # Create backup
        backup_path = urdf_path.with_suffix('.urdf.bak')
        shutil.copy2(urdf_path, backup_path)
        print(f"\nCreated backup at: {backup_path}")

        # Write updated URDF
        tree.write(urdf_path, encoding='utf-8', xml_declaration=True)
        print(f"Updated URDF saved to: {urdf_path}")

    print(f"\nTotal paths {'would be ' if dry_run else ''}changed: {changes}")

def main():
    parser = argparse.ArgumentParser(description='Update mesh paths in URDF file')
    parser.add_argument('urdf_file', help='Path to URDF file')
    parser.add_argument('--prefix', default='../meshes',
                       help='New prefix for mesh paths (default: ../meshes)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be done without making changes')
    args = parser.parse_args()

    urdf_path = Path(args.urdf_file)

    if not urdf_path.exists():
        print(f"Error: URDF file not found: {urdf_path}")
        sys.exit(1)

    if args.dry_run:
        print("\nDRY RUN - No changes will be made")

    # Update mesh paths
    update_mesh_paths(urdf_path, args.prefix, args.dry_run)

if __name__ == "__main__":
    main()
