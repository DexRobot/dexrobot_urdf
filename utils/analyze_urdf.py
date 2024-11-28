#!/usr/bin/env python3

import sys
import xml.etree.ElementTree as ET
import numpy as np
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict
import argparse

@dataclass
class Origin:
    xyz: np.ndarray
    rpy: np.ndarray

    @classmethod
    def from_xml(cls, element) -> Optional['Origin']:
        if element is None:
            return None

        # Get origin element
        origin = element.find('origin')
        if origin is None:
            return None

        # Parse xyz
        xyz_str = origin.get('xyz', '0 0 0')
        xyz = np.array([float(x) for x in xyz_str.split()])

        # Parse rpy
        rpy_str = origin.get('rpy', '0 0 0')
        rpy = np.array([float(x) for x in rpy_str.split()])

        return cls(xyz, rpy)

@dataclass
class LinkOrigins:
    link_name: str
    visual: Optional[Origin]
    collision: Optional[Origin]

@dataclass
class InertiaData:
    link_name: str
    matrix: np.ndarray
    diagonal: np.ndarray
    mass: float

def extract_origins(urdf_path: str) -> List[LinkOrigins]:
    """Extract visual and collision origins from URDF file."""
    tree = ET.parse(urdf_path)
    root = tree.getroot()

    origins = []
    for link in root.findall('.//link'):
        link_name = link.get('name')

        # Get origins from visual and collision elements
        visual = Origin.from_xml(link.find('visual'))
        collision = Origin.from_xml(link.find('collision'))

        origins.append(LinkOrigins(link_name, visual, collision))

    return origins

def extract_inertias(urdf_path: str) -> List[InertiaData]:
    """Extract inertia matrices from URDF file."""
    tree = ET.parse(urdf_path)
    root = tree.getroot()

    inertias = []
    for link in root.findall('.//link'):
        link_name = link.get('name')
        inertial = link.find('inertial')
        if inertial is None:
            continue

        # Get mass
        mass_elem = inertial.find('mass')
        if mass_elem is None:
            continue
        mass = float(mass_elem.get('value'))

        # Get inertia
        inertia = inertial.find('inertia')
        if inertia is None:
            continue

        # Extract values
        ixx = float(inertia.get('ixx'))
        ixy = float(inertia.get('ixy'))
        ixz = float(inertia.get('ixz'))
        iyy = float(inertia.get('iyy'))
        iyz = float(inertia.get('iyz'))
        izz = float(inertia.get('izz'))

        # Create symmetric matrix
        matrix = np.array([
            [ixx, ixy, ixz],
            [ixy, iyy, iyz],
            [ixz, iyz, izz]
        ])

        diagonal = np.array([ixx, iyy, izz])

        inertias.append(InertiaData(link_name, matrix, diagonal, mass))

    return inertias

def is_positive_definite(matrix: np.ndarray, tol: float = 1e-10) -> Tuple[bool, List[float]]:
    """Check if matrix is positive definite by computing eigenvalues."""
    eigenvals = np.linalg.eigvals(matrix)
    return np.all(eigenvals > -tol), eigenvals.tolist()

def check_triangle_inequalities(diagonal: np.ndarray, tol: float = 1e-10) -> Tuple[bool, List[bool]]:
    """Check triangle inequalities for principal moments."""
    ixx, iyy, izz = diagonal
    checks = [
        ixx + iyy >= izz - tol,
        iyy + izz >= ixx - tol,
        izz + ixx >= iyy - tol
    ]
    return all(checks), checks

def check_origin_consistency(origins: List[LinkOrigins], tol: float = 1e-6) -> Dict[str, List[str]]:
    """Check consistency between visual and collision origins."""
    issues = {}

    for link in origins:
        link_issues = []

        # Helper function to format origin for display
        def format_origin(o: Optional[Origin]) -> str:
            if o is None:
                return "None"
            return f"xyz: [{', '.join(f'{x:.6f}' for x in o.xyz)}], rpy: [{', '.join(f'{x:.6f}' for x in o.rpy)}]"

        # Only compare visual and collision origins if both exist
        if link.visual is not None and link.collision is not None:
            # Check xyz
            if not np.allclose(link.visual.xyz, link.collision.xyz, atol=tol):
                link_issues.append("Inconsistent visual vs collision xyz:")
                link_issues.append(f"  Visual:    {format_origin(link.visual)}")
                link_issues.append(f"  Collision: {format_origin(link.collision)}")

            # Check rpy
            # Consider 2π periodicity for rotations
            vis_rpy_mod = link.visual.rpy % (2 * np.pi)
            col_rpy_mod = link.collision.rpy % (2 * np.pi)
            if not np.allclose(vis_rpy_mod, col_rpy_mod, atol=tol):
                link_issues.append("Inconsistent visual vs collision rpy:")
                link_issues.append(f"  Visual:    {format_origin(link.visual)}")
                link_issues.append(f"  Collision: {format_origin(link.collision)}")

        if link_issues:
            issues[link.link_name] = link_issues

    return issues

def analyze_urdf(urdf_path: str) -> None:
    """Analyze URDF file for various issues."""
    print("\n=== URDF Analysis ===")

    # Extract and analyze inertias
    inertias = extract_inertias(urdf_path)

    # Track issues
    pd_issues = []
    triangle_issues = []
    suspicious_values = []

    for data in inertias:
        # Check positive definiteness
        is_pd, eigenvals = is_positive_definite(data.matrix)
        if not is_pd:
            pd_issues.append((data, eigenvals))

        # Check triangle inequalities
        satisfies_triangle, checks = check_triangle_inequalities(data.diagonal)
        if not satisfies_triangle:
            triangle_issues.append((data, checks))

        # Check for suspicious values
        max_val = np.max(np.abs(data.diagonal))
        min_val = np.min(np.abs(data.diagonal))
        if min_val > 0 and max_val/min_val > 1e6:
            suspicious_values.append((data, max_val/min_val))

    # Check origin consistency
    origins = extract_origins(urdf_path)
    origin_issues = check_origin_consistency(origins)

    # Report findings
    if pd_issues:
        print("\nLinks with non-positive definite inertia matrices:")
        for data, eigenvals in pd_issues:
            print(f"- {data.link_name}:")
            print(f"  Mass: {data.mass}")
            print(f"  Eigenvalues: {[f'{ev:.2e}' for ev in eigenvals]}")
            print(f"  Matrix:\n{data.matrix}")

    if triangle_issues:
        print("\nLinks violating triangle inequalities:")
        for data, checks in triangle_issues:
            print(f"- {data.link_name}:")
            print(f"  Mass: {data.mass}")
            print(f"  Principal moments: [{', '.join(f'{x:.2e}' for x in data.diagonal)}]")
            inequalities = [
                "Ixx + Iyy >= Izz",
                "Iyy + Izz >= Ixx",
                "Izz + Ixx >= Iyy"
            ]
            for ineq, check in zip(inequalities, checks):
                if not check:
                    print(f"  Failed: {ineq}")

    if suspicious_values:
        print("\nLinks with suspicious inertia ratios:")
        for data, ratio in suspicious_values:
            print(f"- {data.link_name}:")
            print(f"  Mass: {data.mass}")
            print(f"  Principal moments: [{', '.join(f'{x:.2e}' for x in data.diagonal)}]")
            print(f"  Max/min ratio: {ratio:.2e}")

    if origin_issues:
        print("\nLinks with inconsistent origins:")
        for link_name, issues in origin_issues.items():
            print(f"\n- {link_name}:")
            for issue in issues:
                print(f"  {issue}")

    if not any([pd_issues, triangle_issues, suspicious_values, origin_issues]):
        print("\nNo issues found!")

def main():
    parser = argparse.ArgumentParser(description='Analyze URDF for physical validity and consistency')
    parser.add_argument('urdf_file', help='Path to URDF file')
    args = parser.parse_args()

    try:
        analyze_urdf(args.urdf_file)
    except Exception as e:
        print(f"Error processing URDF file: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
