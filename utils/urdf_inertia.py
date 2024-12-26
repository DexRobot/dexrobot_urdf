import numpy as np
import trimesh
import xml.etree.ElementTree as ET
import re
from typing import Dict, Pattern

class DensityMatcher:
    def __init__(self, density_map: Dict[str, float], default_density: float = 1000):
        """
        Initialize density matcher with regex patterns and densities.

        Args:
            density_map: Dictionary mapping regex patterns to densities (kg/m³)
            default_density: Default density if no pattern matches (kg/m³)
        """
        self.default_density = default_density
        self.patterns = [(re.compile(pattern), density)
                        for pattern, density in density_map.items()]

    def get_density(self, link_name: str, mesh_path: str) -> float:
        """
        Get density based on link name and mesh path.

        Args:
            link_name: Name of the URDF link
            mesh_path: Path to the mesh file

        Returns:
            float: Matching density or default density
        """
        # Try matching against link name first, then mesh path
        for pattern, density in self.patterns:
            if pattern.search(link_name) or pattern.search(mesh_path):
                return density
        return self.default_density

def calculate_mesh_inertia(mesh_path: str, density: float) -> tuple:
    """
    Calculate mass and inertia tensor for a mesh file.

    Args:
        mesh_path: Path to the mesh file (STL, OBJ, etc.)
        density: Material density in kg/m³

    Returns:
        tuple: (mass, inertia_tensor, center_of_mass)
    """
    mesh = trimesh.load(mesh_path)
    volume = mesh.volume
    mass = volume * density
    center_of_mass = mesh.center_mass
    inertia = density * mesh.moment_inertia

    return mass, inertia, center_of_mass

def update_urdf_inertials(urdf_path: str,
                         density_map: Dict[str, float] = None,
                         default_density: float = 1000,
                         output_path: str = None):
    """
    Update URDF file with calculated inertial properties.

    Args:
        urdf_path: Path to input URDF file
        density_map: Dictionary mapping regex patterns to densities
        default_density: Default density if no pattern matches
        output_path: Path for output URDF. If None, modifies input file
    """
    if density_map is None:
        density_map = {}

    if output_path is None:
        output_path = urdf_path

    density_matcher = DensityMatcher(density_map, default_density)

    # Parse URDF
    tree = ET.parse(urdf_path)
    root = tree.getroot()

    # Track masses for reporting
    link_masses = {}

    # Process each link
    for link in root.findall('link'):
        link_name = link.get('name', '')
        visual = link.find('visual')
        if visual is None:
            continue

        # Find mesh
        mesh = visual.find('geometry/mesh')
        if mesh is None:
            continue

        mesh_path = mesh.get('filename')
        if not mesh_path:
            continue

        # Get density for this link/mesh
        density = density_matcher.get_density(link_name, mesh_path)

        # Calculate inertial properties
        mass, inertia, com = calculate_mesh_inertia(mesh_path, density)
        link_masses[link_name] = (mass, density)

        # Create or update inertial element
        inertial = link.find('inertial')
        if inertial is None:
            inertial = ET.SubElement(link, 'inertial')

        # Update mass
        mass_elem = inertial.find('mass')
        if mass_elem is None:
            mass_elem = ET.SubElement(inertial, 'mass')
        mass_elem.set('value', str(mass))

        # Update origin (center of mass)
        origin = inertial.find('origin')
        if origin is None:
            origin = ET.SubElement(inertial, 'origin')
        origin.set('xyz', f"{com[0]} {com[1]} {com[2]}")
        origin.set('rpy', "0 0 0")

        # Update inertia tensor
        inertia_elem = inertial.find('inertia')
        if inertia_elem is None:
            inertia_elem = ET.SubElement(inertial, 'inertia')

        # Set inertia values
        inertia_elem.set('ixx', str(inertia[0][0]))
        inertia_elem.set('ixy', str(inertia[0][1]))
        inertia_elem.set('ixz', str(inertia[0][2]))
        inertia_elem.set('iyy', str(inertia[1][1]))
        inertia_elem.set('iyz', str(inertia[1][2]))
        inertia_elem.set('izz', str(inertia[2][2]))

    # Print mass report
    print("\nMass Report:")
    print("-" * 60)
    print(f"{'Link Name':<30} {'Mass (kg)':<12} {'Density (kg/m³)':<15}")
    print("-" * 60)

    total_mass = 0
    for link_name, (mass, density) in sorted(link_masses.items()):
        print(f"{link_name:<30} {mass:<12.3f} {density:<15.1f}")
        total_mass += mass

    print("-" * 60)
    print(f"{'Total Mass:':<30} {total_mass:<12.3f}")

    # Write updated URDF
    tree.write(output_path, encoding='utf-8', xml_declaration=True)

if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description='Calculate and update URDF inertial properties')
    parser.add_argument('urdf_path', help='Path to input URDF file')
    parser.add_argument('--density-map', type=str,
                        help='JSON file with regex patterns mapping to densities')
    parser.add_argument('--default-density', type=float, default=1000.0,
                        help='Default density in kg/m³ (default: 1000)')
    parser.add_argument('--output', help='Output URDF path (optional)')

    args = parser.parse_args()

    # Load density map if provided
    density_map = {}
    if args.density_map:
        with open(args.density_map, 'r') as f:
            density_map = json.load(f)

    update_urdf_inertials(args.urdf_path,
                         density_map=density_map,
                         default_density=args.default_density,
                         output_path=args.output)
