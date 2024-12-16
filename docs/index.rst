Welcome to DexRobot URDF Models's documentation!
=================================================

This repository contains URDF models for a dexterous robotic hand
system, including both left and right hand configurations. The models
are compatible with standard URDF toolchains and have been tested with
MuJoCo.

.. toctree::
   :maxdepth: 2
   :caption: Contents

Quickstart
----------

The URDF models can be visualized using MuJoCo’s ``simulate`` tool:

.. code:: bash

   # For left hand
   simulate urdf/dexhand021_left.urdf

   # For right hand
   simulate urdf/dexhand021_right.urdf

Note: After launching the simulator, hit the ‘Pause’ button first, then
‘Reset’ to properly visualize the model in its initial configuration.

Models
------

Full Model
~~~~~~~~~~

The full model provides high-fidelity mesh files suitable for rendering
and visualization. It includes detailed geometry for all components of
the hand.

Simplified Model
~~~~~~~~~~~~~~~~

A simplified version optimized for simulation is also provided. This
model reduces geometric complexity while maintaining kinematic accuracy,
making it more efficient for physics simulations. Solidworks project
files for these simplified models are included in the repository.

Model Conventions
-----------------

Naming Convention
~~~~~~~~~~~~~~~~~

The model follows a systematic naming convention for links and joints:

-  Base Format: ``[lr]_[type]_[component]``

   -  ``[lr]``: ‘l’ for left hand, ‘r’ for right hand
   -  ``[type]``: ‘p’ for palm components, ‘f’ for finger components
   -  ``[component]``: specific component identifier

Component Numbering
^^^^^^^^^^^^^^^^^^^

-  Thumb Rotation: ``*_1_1``
-  Finger Spread: ``[2345]_1`` (for index, middle, ring, and pinky
   fingers)
-  Metacarpophalangeal (MCP) Joints: ``[12345]_2``
-  Proximal & Distal Joints: ``[12345]_[34]`` (for all fingers)

   -  Note: While proximal and distal joints are mechanically coupled in
      the physical system, this coupling is not reflected in the URDF
      model

Frame Convention
~~~~~~~~~~~~~~~~

The model primarily follows the Denavit-Hartenberg (DH) convention for
frame assignments:

Base Frame
^^^^^^^^^^

-  Origin: Located at the wrist
-  Z-axis: Points toward fingertips
-  Thumb Orientation: Inclines toward negative X-axis for both hands

Additional Resources
--------------------

The repository includes utility scripts in the utils/ directory for URDF
file processing and analysis. These tools can help with tasks such as
updating mesh paths and analyzing model properties.

Notes for Users
---------------

-  Mesh files are referenced relative to the URDF location using
   ``../meshes/``
-  The models are compatible with major robotics simulation environments
   that support URDF
-  While the URDF models don’t enforce joint coupling, users can
   implement this in their control software
-  The utility scripts can be modified as needed to accommodate specific
   requirements
