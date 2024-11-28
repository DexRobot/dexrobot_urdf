# DexRobot URDF Models

This repository contains URDF models for a dexterous robotic hand system, including both left and right hand configurations. The models are compatible with standard URDF toolchains and have been tested with MuJoCo.

## Quickstart

The URDF models can be visualized using MuJoCo's `simulate` tool:

```bash
# For left hand
simulate urdf/dexhand021_left.urdf

# For right hand
simulate urdf/dexhand021_right.urdf
```

Note: After launching the simulator, hit the 'Pause' button first, then 'Reset' to properly visualize the model in its initial configuration.

## Model Conventions

### Naming Convention

The model follows a systematic naming convention for links and joints:

- Base Format: `[lr]_[type]_[component]`
  - `[lr]`: 'l' for left hand, 'r' for right hand
  - `[type]`: 'p' for palm components, 'f' for finger components
  - `[component]`: specific component identifier

#### Component Numbering

- Thumb Rotation: `*_1_1`
- Finger Spread: `[2345]_1` (for index, middle, ring, and pinky fingers)
- Proximal Joints: `[12345]_2` (for all fingers including thumb)
- Distal Joints: `[12345]_[34]` (for all fingers)
  - Note: While distal joints are mechanically coupled in the physical system, this coupling is not reflected in the URDF model

### Frame Convention

The model primarily follows the Denavit-Hartenberg (DH) convention for frame assignments:

#### Base Frame
- Origin: Located at the wrist
- Z-axis: Points toward fingertips
- Thumb Orientation: Inclines toward negative X-axis for both hands

## Utility Scripts

The repository includes several Python utilities in the `utils/` directory for checking and modifying URDF models:

### analyze_urdf.py
Analyzes URDF files for physical validity and consistency:
```bash
python utils/analyze_urdf.py urdf/dexhand021_left.urdf
```

### update_mesh_paths.py
Updates mesh file paths in URDF files:
```bash
python utils/update_mesh_paths.py urdf/dexhand021_left.urdf --prefix ../meshes
```

### rename_urdf.py
Renames links and joints in URDF files:
```bash
python utils/rename_urdf.py urdf/dexhand021_left.urdf meshes/
```

All utility scripts support a `--dry-run` option to preview changes without modifying files.

## Notes for Users

- Mesh files are referenced relative to the URDF location using `../meshes/`
- The models are compatible with major robotics simulation environments that support URDF
- While the URDF models don't enforce joint coupling, users can implement this in their control software
- The utility scripts can be modified as needed to accommodate specific requirements
