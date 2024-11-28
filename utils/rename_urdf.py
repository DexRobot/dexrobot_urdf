#!/usr/bin/env python3

import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
import argparse
import re
from typing import Dict, Set
import shutil

def create_name_mapping(old_name: str) -> str:
    """Create new name by removing '6_' and handling special cases."""
    # Handle special cases first
    if old_name in ["left_hand_base", "right_hand_base"]:
        return old_name

    # Handle main palm link
    if old_name == "l_f_link6":
        return "l_p_link0"

    if old_name == "r_f_link6":
        return "r_p_link0"

    # Handle palm components specially
    palm_match = re.match(r'([lr])_f_link6_([123456])$', old_name)
    if palm_match:
        return f'{palm_match.group(1)}_p_link{palm_match.group(2)}'

    # For all other cases, remove '6_'
    new_name = old_name.replace('6_', '')
    return new_name

def rename_meshes(mesh_dir: Path, name_mapping: Dict[str, str], dry_run: bool = False) -> None:
    """Rename mesh files according to the mapping."""
    print("\n=== Renaming Mesh Files ===")

    # Get all STL files
    stl_files = list(mesh_dir.glob("*.STL"))
    if not stl_files:
        print(f"No STL files found in {mesh_dir}")
        return

    renamed = 0
    for mesh_path in stl_files:
        old_name = mesh_path.stem
        # Find if this mesh name corresponds to any link
        new_name = None
        for old_link, new_link in name_mapping.items():
            if old_name.endswith(old_link):
                new_name = old_name.replace(old_link, new_link)
                break

        if new_name:
            new_path = mesh_path.with_name(f"{new_name}.STL")
            if dry_run:
                print(f"Would rename: {mesh_path.name} -> {new_path.name}")
            else:
                try:
                    mesh_path.rename(new_path)
                    print(f"Renamed: {mesh_path.name} -> {new_path.name}")
                    renamed += 1
                except Exception as e:
                    print(f"Error renaming {mesh_path}: {e}")

    print(f"\nTotal files {'would be ' if dry_run else ''}renamed: {renamed}")

def update_urdf(urdf_path: Path, name_mapping: Dict[str, str], dry_run: bool = False) -> None:
    """Update URDF with new names."""
    print("\n=== Updating URDF ===")

    # Parse URDF
    tree = ET.parse(urdf_path)
    root = tree.getroot()

    # Track changes
    changes = 0

    # Update link names
    for link in root.findall(".//link"):
        old_name = link.get('name')
        if old_name in name_mapping:
            link.set('name', name_mapping[old_name])
            changes += 1

    # Update joint parent/child references
    for joint in root.findall(".//joint"):
        parent = joint.find("parent")
        child = joint.find("child")

        if parent is not None and parent.get('link') in name_mapping:
            parent.set('link', name_mapping[parent.get('link')])
            changes += 1

        if child is not None and child.get('link') in name_mapping:
            child.set('link', name_mapping[child.get('link')])
            changes += 1

        # Update joint names if they follow the same pattern
        old_name = joint.get('name')
        if old_name:
            new_name = create_name_mapping(old_name)
            if old_name != new_name:
                joint.set('name', new_name)
                changes += 1

    # Update mesh filenames in visual and collision elements
    for mesh in root.findall(".//mesh"):
        filename = mesh.get('filename')
        if filename:
            # Extract just the filename part
            path, fname = os.path.split(filename)
            base_name = os.path.splitext(fname)[0]

            # Find if this mesh name corresponds to any link
            new_name = None
            for old_link, new_link in name_mapping.items():
                if base_name.endswith(old_link):
                    new_name = base_name.replace(old_link, new_link)
                    break

            if new_name:
                new_filename = os.path.join(path, f"{new_name}.STL")
                mesh.set('filename', new_filename)
                changes += 1

    if not dry_run:
        # Create backup
        backup_path = urdf_path.with_suffix('.urdf.bak')
        shutil.copy2(urdf_path, backup_path)
        print(f"Created backup at: {backup_path}")

        # Write updated URDF
        tree.write(urdf_path, encoding='utf-8', xml_declaration=True)
        print(f"Updated URDF saved to: {urdf_path}")

    print(f"Total changes {'would be ' if dry_run else ''}made: {changes}")

def main():
    parser = argparse.ArgumentParser(description='Rename URDF links and corresponding mesh files')
    parser.add_argument('urdf_file', help='Path to URDF file')
    parser.add_argument('mesh_dir', help='Path to mesh directory')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be done without making changes')
    args = parser.parse_args()

    urdf_path = Path(args.urdf_file)
    mesh_dir = Path(args.mesh_dir)

    if not urdf_path.exists():
        print(f"Error: URDF file not found: {urdf_path}")
        sys.exit(1)

    if not mesh_dir.exists():
        print(f"Error: Mesh directory not found: {mesh_dir}")
        sys.exit(1)

    # Parse URDF to get all link names
    tree = ET.parse(urdf_path)
    root = tree.getroot()

    # Create name mapping
    name_mapping = {}
    for link in root.findall(".//link"):
        old_name = link.get('name')
        new_name = create_name_mapping(old_name)
        if old_name != new_name:
            name_mapping[old_name] = new_name

    # Print rename plan
    print("=== Rename Plan ===")
    print("\nLink renames:")
    for old, new in sorted(name_mapping.items()):
        print(f"{old} -> {new}")

    if args.dry_run:
        print("\nDRY RUN - No changes will be made")

    # Rename mesh files
    rename_meshes(mesh_dir, name_mapping, args.dry_run)

    # Update URDF
    update_urdf(urdf_path, name_mapping, args.dry_run)

if __name__ == "__main__":
    main()
