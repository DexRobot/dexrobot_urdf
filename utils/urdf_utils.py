import urdf_parser_py.urdf as urdf
import re
import numpy as np


def get_dof_names(urdf_path):
    robot = urdf.URDF.from_xml_file(urdf_path)
    return [joint.name for joint in robot.joints if joint.type != "fixed"]


def get_link_by_name(robot, name):
    for link in robot.links:
        if link.name == name:
            return link
    return None

def get_joint_by_name(robot, name):
    for joint in robot.joints:
        if joint.name == name:
            return joint
    return None

def print_link_properties(link):
    # Print inertial properties
    if link.inertial:
        print("Inertial Properties:")
        print(f"  Mass: {link.inertial.mass}")
        print(f"  Inertia Tensor:")
        print(f"    Ixx: {link.inertial.inertia.ixx}")
        print(f"    Ixy: {link.inertial.inertia.ixy}")
        print(f"    Ixz: {link.inertial.inertia.ixz}")
        print(f"    Iyy: {link.inertial.inertia.iyy}")
        print(f"    Iyz: {link.inertial.inertia.iyz}")
        print(f"    Izz: {link.inertial.inertia.izz}")
        print(f"  Center of Mass (xyz): {link.inertial.origin.xyz}")
        print(f"  Orientation (rpy): {link.inertial.origin.rpy}")

    # Print visual properties
    if link.visual:
        print("Visual Properties:")
        print(f"  Geometry Type: {type(link.visual.geometry)}")
        if isinstance(link.visual.geometry, urdf.Mesh):
            print(f"  Mesh Filename: {link.visual.geometry.filename}")
        print(f"  Visual Origin (xyz): {link.visual.origin.xyz}")
        print(f"  Visual Origin (rpy): {link.visual.origin.rpy}")
        if link.visual.material:
            print(f"  Material Name: {link.visual.material.name}")
            if link.visual.material.color:
                print(f"  Color RGBA: {link.visual.material.color.rgba}")
            if link.visual.material.texture:
                print(f"  Texture Filename: {link.visual.material.texture.filename}")

    # Print collision properties
    if link.collision:
        print("Collision Properties:")
        print(f"  Geometry Type: {type(link.collision.geometry)}")
        if isinstance(link.collision.geometry, urdf.Mesh):
            print(f"  Collision Mesh Filename: {link.collision.geometry.filename}")
        print(f"  Collision Origin (xyz): {link.collision.origin.xyz}")
        print(f"  Collision Origin (rpy): {link.collision.origin.rpy}")


def extract_subtree(
    robot,
    start_link_name,
    new_name=None,
):
    # Find the starting link
    start_link = get_link_by_name(robot, start_link_name)
    start_link.origin
    if not start_link:
        print("Link not found.")
        return None

    # Initialize new robot model
    new_robot = urdf.URDF()
    if new_name is None:
        new_robot.name = robot.name + "_subpart"
    else:
        new_robot.name = new_name

    # Function to recursively add links and joints
    def add_link_and_joints(current_link):
        # Add current link
        new_robot.add_link(current_link)

        # Find and add joints where current_link is a parent
        for joint in robot.joints:
            if joint.parent == current_link.name:
                new_robot.add_joint(joint)
                child_link = get_link_by_name(robot, joint.child)
                if child_link:
                    add_link_and_joints(child_link)

    add_link_and_joints(start_link)
    return new_robot


def remove_links_and_descendants(robot, re_link_names_to_remove, new_name=None):
    """
    Remove a link and all its descendants from the URDF model. Used for extracting the "trunk" part of a robot.

    Args:
    robot (urdf.URDF): The original URDF robot model (will not be modified).
    re_link_names_to_remove (list): A list of regular expressions to match the link names to remove.
    new_name (str, optional): The name of the new robot model. Defaults to None.

    Returns:
    urdf.URDF: The new URDF model with the specified links removed.
    """
    to_remove = []

    for pattern in re_link_names_to_remove:
        for link in robot.links:
            if re.match(pattern, link.name):
                to_remove.append(link.name)

    index = 0

    # Find all descendants of the link
    while index < len(to_remove):
        current_link = to_remove[index]
        for joint in robot.joints:
            if joint.parent == current_link:
                if joint.child not in to_remove:
                    to_remove.append(joint.child)
        index += 1

    print("Removed links:", to_remove)

    # Remove all links and joints associated with the to_remove list
    remaining_joints = [
        j
        for j in robot.joints
        if j.parent not in to_remove and j.child not in to_remove
    ]
    remaining_links = [l for l in robot.links if l.name not in to_remove]

    new_robot = urdf.URDF()
    if new_name is None:
        new_robot.name = robot.name + "_subpart"
    else:
        new_robot.name = new_name

    # Add remaining links and joints
    print("Remaining links:", list(map(lambda x: x.name, remaining_links)))
    print("Remaining joints:", list(map(lambda x: x.name, remaining_joints)))

    # Function to recursively add links and joints
    def add_link_and_joints(current_link):
        # Add current link
        new_robot.add_link(current_link)

        # Find and add joints where current_link is a parent
        for joint in remaining_joints:
            if joint.parent == current_link.name:
                new_robot.add_joint(joint)
                child_link = get_link_by_name(robot, joint.child)
                if child_link in remaining_links:
                    add_link_and_joints(child_link)

    add_link_and_joints(remaining_links[0])

    return new_robot


def replace_mesh_paths(robot, new_prefix):
    """
    Replace the paths of mesh files in the URDF with the specified prefix.

    Parameters:
    robot (urdf.URDF): The URDF robot model.
    new_prefix (str): The new prefix to use for the mesh file paths.

    Returns:
    None
    """

    def update_mesh_path(visual_or_collision):
        if isinstance(visual_or_collision.geometry, urdf.Mesh):
            filename = visual_or_collision.geometry.filename
            new_filename = f"{new_prefix}/{filename.split('/')[-1]}"
            visual_or_collision.geometry.filename = new_filename

    for link in robot.links:
        # Update visual mesh paths
        if link.visual:
            update_mesh_path(link.visual)

        # Update collision mesh paths
        if link.collision:
            update_mesh_path(link.collision)


def replace_mesh_paths_by_category(robot, category_prefix_map):
    """
    Replace the paths of mesh files in the URDF with category-specific prefixes.

    Parameters:
    robot (urdf.URDF): The URDF robot model.
    category_prefix_map (dict): A dictionary mapping regex patterns to prefixes.

    Returns:
    None
    """
    def update_mesh_path(visual_or_collision, link_name):
        if isinstance(visual_or_collision.geometry, urdf.Mesh):
            filename = visual_or_collision.geometry.filename
            for pattern, prefix in category_prefix_map.items():
                if re.match(pattern, link_name):
                    new_filename = f"{prefix}/{filename.split('/')[-1]}"
                    visual_or_collision.geometry.filename = new_filename
                    break

    for link in robot.links:
        # Update visual mesh paths
        if link.visual:
            update_mesh_path(link.visual, link.name)

        # Update collision mesh paths
        if link.collision:
            update_mesh_path(link.collision, link.name)


def categorize_joints_by_type(robot):
    """
    Extracts all joint names from the URDF model and categorizes them by joint type.

    Parameters:
    robot (urdf.URDF): The URDF robot model.

    Returns:
    dict: A dictionary where keys are joint types and values are lists of joint names of that type.
    """
    joint_dict = {}
    for joint in robot.joints:
        # If the joint type is not yet in the dictionary, add it with an empty list
        if joint.type not in joint_dict:
            joint_dict[joint.type] = []
        # Append the joint name to the corresponding type list
        joint_dict[joint.type].append(joint.name)

    return joint_dict


def add_virtual_end_effector(robot, parent_link_name, ee_name, xyz, rpy):
    """
    Adds a virtual end effector link to the robot.

    Parameters:
    robot (urdf.URDF): The URDF robot model.
    parent_link_name (str): The name of the parent link.
    ee_name (str): The name of the new virtual end effector link.
    xyz (list of float): The position [x, y, z] of the end effector relative to the parent link.
    rpy (list of float): The orientation [roll, pitch, yaw] of the end effector relative to the parent link.

    Returns: None.
    """
    # Create the new end effector link
    ee_link = urdf.Link(
        name=ee_name,
        visual=urdf.Visual(
            geometry=urdf.Sphere(radius=0.01),
            material=urdf.Material(name="green", color=urdf.Color([0, 1, 0, 1])),
        ),
    )

    # Create the fixed joint connecting the parent link to the new end effector link
    ee_joint = urdf.Joint(
        name=f"{parent_link_name}_to_{ee_name}",
        parent=parent_link_name,
        child=ee_name,
        joint_type="fixed",
        origin=urdf.Pose(xyz=xyz, rpy=rpy),
    )

    # Add the new link and joint to the robot
    robot.add_link(ee_link)
    robot.add_joint(ee_joint)

def translate_frame(robot, joint_or_link_name, xyz_offset, rpy=None):
    """
    Move the origin of link or joint.

    Parameters:
    robot (urdf.URDF): The URDF robot model.
    joint_or_link_name (str): The name of the joint or link.
    xyz_offset (np.array): The offset to move the origin by.

    Returns:
    None
    """
    link = get_link_by_name(robot, joint_or_link_name)
    if link:
        link.inertial.origin.xyz = list(np.array(link.inertial.origin.xyz) + xyz_offset)
        link.visual.origin.xyz = list(np.array(link.visual.origin.xyz) + xyz_offset)
        link.collision.origin.xyz = list(np.array(link.collision.origin.xyz) + xyz_offset)
        return
    else:
        joint = get_joint_by_name(robot, joint_or_link_name)
        if joint:
            joint.origin.xyz = list(np.array(joint.origin.xyz) + xyz_offset)
            return

    print("Link or joint not found.")


def print_urdf_tree(urdf_file_path, root_link_name=None):
    """
    Print the tree structure of a URDF file.

    Args:
    urdf_file_path (str): Path to the URDF file.
    root_link_name (str, optional): Name of the root link. If None, the first link in the URDF is used.

    Returns:
    None
    """
    robot = urdf.URDF.from_xml_file(urdf_file_path)

    if root_link_name is None:
        root_link_name = robot.links[0].name

    def print_tree(link_name, level=0):
        print("  " * level + "- " + link_name)
        for joint in robot.joints:
            if joint.parent == link_name:
                print("  " * (level + 1) + "└─ " + joint.name + " (" + joint.type + ")")
                print_tree(joint.child, level + 2)

    print(f"URDF Tree Structure for {urdf_file_path}:")
    print_tree(root_link_name)
