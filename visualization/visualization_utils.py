"""Functions for plotting graphs with community highlighting and traversal paths."""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from scipy.spatial import ConvexHull, QhullError
from scipy.spatial.distance import pdist, squareform
from typing import List, Tuple, Dict, Optional


from visualization.graph_plot_data_utils import prepare_traversal_arrows, ensure_node_labels

# --- Constants for Community Highlighting ---
# Consider making these configurable if needed
DEFAULT_HULL_PADDING_SCALE_FACTOR = (
    1.1  # Scaling factor for hull points relative to centroid
)
DEFAULT_MIN_COMMUNITY_PADDING = 0.4  # Fixed padding/width/radius (absolute units)
DEFAULT_LINEARITY_THRESHOLD = 0.5  # Hull area threshold to detect linear arrangement
DEFAULT_COMMUNITY_ALPHA = 0.15  # Background transparency for community shapes
DEFAULT_COMMUNITY_EDGE_ALPHA = 0.5  # Edge transparency for community shapes
DEFAULT_COMMUNITY_LINEWIDTH = 1.5
DEFAULT_COMMUNITY_LINESTYLE = "--"
DEFAULT_ARROW_SHRINK_FACTOR_REL_TO_NODE_SIZE = (
    0.5  # How much arrow shrinks (relative to node radius)
)
DEFAULT_ARROW_LW = 2
DEFAULT_ARROW_MUTATION_SCALE = 20
DEFAULT_ARROW_CONNECTION_STYLE = "arc3,rad=0.3"


def calculate_community_patch(
    community_nodes: List[int],
    layout_coords: Dict[int, Tuple[float, float]],
    graph_vcount: int,
    color_rgba: Tuple[float, float, float, float],
    hull_padding_scale_factor: float = DEFAULT_HULL_PADDING_SCALE_FACTOR,
    min_community_padding: float = DEFAULT_MIN_COMMUNITY_PADDING,
    linearity_threshold: float = DEFAULT_LINEARITY_THRESHOLD,
    community_alpha: float = DEFAULT_COMMUNITY_ALPHA,
    community_edge_alpha: float = DEFAULT_COMMUNITY_EDGE_ALPHA,
    linewidth: float = DEFAULT_COMMUNITY_LINEWIDTH,
    linestyle: str = DEFAULT_COMMUNITY_LINESTYLE,
) -> Optional[mpatches.Patch]:
    """
    Calculates the matplotlib Patch (Polygon or Circle) for a single community.

    Handles cases for 1, 2, or >=3 nodes, including linear arrangements.

    Args:
        community_nodes: List of node indices in the community.
        layout_coords: Dictionary mapping node index to (x, y) coordinates.
        graph_vcount: Total number of vertices in the graph (for validation).
        color_rgba: Base RGBA color for the community.
        hull_padding_scale_factor: Scaling factor for hull points.
        min_community_padding: Fixed padding/width/radius.
        linearity_threshold: Hull area threshold for detecting linearity.
        community_alpha: Alpha for the patch face color.
        community_edge_alpha: Alpha for the patch edge color.
        linewidth: Line width for the patch edge.
        linestyle: Line style for the patch edge.


    Returns:
        A matplotlib.patches.Patch object or None if the community is empty
        or cannot be drawn.
    """
    valid_nodes_in_community = [
        node_id
        for node_id in community_nodes
        if 0 <= node_id < graph_vcount and node_id in layout_coords
    ]
    num_valid_nodes = len(valid_nodes_in_community)

    if num_valid_nodes == 0:
        print(f"  Skipping community: No valid nodes found in layout.")
        return None

    comm_coords = [layout_coords[node_id] for node_id in valid_nodes_in_community]
    coords_array = np.array(comm_coords)

    patch_to_add = None
    face_color_with_alpha = (*color_rgba[:3], community_alpha)
    edge_color = (*color_rgba[:3], community_edge_alpha)
    patch_kwargs = dict(
        facecolor=face_color_with_alpha,
        edgecolor=edge_color,
        linewidth=linewidth,
        linestyle=linestyle,
        zorder=-1,
    )  # Draw behind nodes/edges

    treat_as_linear = False  # Flag to indicate using capsule logic for >= 3 nodes

    # --- Polygon Logic (>= 3 nodes) ---
    if num_valid_nodes >= 3:
        try:
            # Add small jitter only if points are potentially collinear/duplicate
            unique_coords, counts = np.unique(coords_array, axis=0, return_counts=True)
            if len(unique_coords) < 3:
                # Use jitter only if needed to form a hull
                coords_array_processed = coords_array + np.random.normal(
                    0, 0.001, coords_array.shape
                )
                print(
                    f"    Community (Nodes: {valid_nodes_in_community}) has < 3 unique points. Applied jitter."
                )
            else:
                coords_array_processed = coords_array  # Use original points

            hull = ConvexHull(
                coords_array_processed
            )  # Calculate hull on potentially jittered points

            # Use original points for area check and padding calculation
            original_hull_points = coords_array[hull.vertices]
            # Check area using original points if possible
            # Need at least 3 unique points for a meaningful area check
            if len(np.unique(original_hull_points, axis=0)) >= 3:
                # Recalculate hull on original points *just* for area check if needed
                # This avoids treating slightly jittered points as non-linear
                try:
                    check_hull = ConvexHull(original_hull_points)
                    hull_area = check_hull.volume  # Area for 2D hull
                except QhullError:
                    hull_area = 0  # Treat as linear if original points fail hull
            else:
                hull_area = 0  # Treat as linear if not enough unique points

            if hull_area < linearity_threshold:
                print(
                    f"    Community (Nodes: {valid_nodes_in_community}) appears linear (hull area {hull_area:.2g} < {linearity_threshold}). Using capsule."
                )
                treat_as_linear = True
            else:
                # --- Standard Hull Padding ---
                hull_coords = (
                    original_hull_points  # Use original points for hull boundary visual
                )
                centroid = hull_coords.mean(axis=0)
                padded_hull_coords = []
                for pt in hull_coords:
                    vector = pt - centroid
                    norm = np.linalg.norm(vector)
                    if norm < 1e-9:  # Point is effectively the centroid
                        # Just apply fixed padding outwards (arbitrary direction, e.g., [1,0])
                        scaled_pt = pt
                        final_pt = scaled_pt + np.array([min_community_padding, 0.0])
                    else:
                        norm_vector = vector / norm
                        # Scale point relative to centroid
                        scaled_pt = centroid + vector * hull_padding_scale_factor
                        # Add fixed padding along the normal vector
                        final_pt = scaled_pt + norm_vector * min_community_padding
                    padded_hull_coords.append(final_pt)

                polygon_coords = np.array(padded_hull_coords)
                print(
                    f"    Community (Nodes: {valid_nodes_in_community}) calculated convex hull with {len(hull_coords)} vertices. Applying padding."
                )
                patch_to_add = mpatches.Polygon(
                    polygon_coords, closed=True, **patch_kwargs
                )

        except QhullError as e:
            print(
                f"    Community (Nodes: {valid_nodes_in_community}) caused QhullError ({e}). Assuming linear arrangement."
            )
            treat_as_linear = True  # Fallback to linear treatment
        except Exception as e:
            print(
                f"    Skipping Community (Nodes: {valid_nodes_in_community}): Error calculating hull: {e}"
            )
            # Decide if treat_as_linear is a reasonable fallback here too, or just skip. Let's try linear.
            treat_as_linear = (
                True if num_valid_nodes >= 2 else False
            )  # Can only be linear if >= 2 nodes

    # --- Handle Linear Case (2 nodes or >=3 detected as linear) ---
    # This block is entered if num_valid_nodes == 2 OR treat_as_linear is True
    if num_valid_nodes == 2 or (treat_as_linear and num_valid_nodes >= 2):
        if treat_as_linear:  # Might have >= 3 nodes but detected as linear
            print(
                f"    Drawing capsule for linear Community (Nodes: {valid_nodes_in_community})"
            )
            # Find the two points farthest apart in the original set
            if num_valid_nodes > 2:
                dist_matrix = squareform(pdist(coords_array, "euclidean"))
                max_dist_idx = np.unravel_index(
                    np.argmax(dist_matrix, axis=None), dist_matrix.shape
                )
                p1 = coords_array[max_dist_idx[0]]
                p2 = coords_array[max_dist_idx[1]]
            else:  # Exactly 2 nodes, treat_as_linear might be False but num_valid_nodes == 2
                p1 = coords_array[0]
                p2 = coords_array[1]
        else:  # Exactly 2 nodes, not explicitly linear, default capsule
            print(
                f"    Drawing capsule for Community (Nodes: {valid_nodes_in_community})"
            )
            p1 = coords_array[0]
            p2 = coords_array[1]

        vec = p2 - p1
        vec_len = np.linalg.norm(vec)

        if vec_len < 1e-6:  # Points are coincident, treat as 1 node case
            print(
                f"    Nodes in Community {valid_nodes_in_community} are (nearly) coincident. Drawing a circle."
            )
            center = coords_array.mean(axis=0)
            radius = min_community_padding
            patch_to_add = mpatches.Circle(center, radius=radius, **patch_kwargs)
        else:
            # Calculate normalized perpendicular vector for width
            perp_vec = np.array([-vec[1], vec[0]]) / vec_len * min_community_padding
            # Calculate normalized parallel vector for length adjustment (slight extension)
            # No need to extend capsule ends if min_community_padding already defines the radius
            norm_vec = vec / vec_len * min_community_padding # Extend by the padding amount

            # Calculate the 4 corners, extending beyond p1 and p2
            corner1 = (p1 - norm_vec) + perp_vec # Back-Left
            corner2 = (p1 - norm_vec) - perp_vec # Back-Right
            corner3 = (p2 + norm_vec) - perp_vec # Front-Right
            corner4 = (p2 + norm_vec) + perp_vec # Front-Left

            # Using Polygon to approximate capsule is simpler than FancyBboxPatch here
            polygon_coords = np.array([corner1, corner2, corner3, corner4])
            patch_to_add = mpatches.Polygon(polygon_coords, closed=True, **patch_kwargs)
            # Note: For a visually perfect capsule, you might need FancyBboxPatch
            # or plot two circles and a rectangle, but Polygon is often sufficient.

    # --- Handle 1 Node Case ---
    elif num_valid_nodes == 1:
        print(f"    Drawing circle for Community (Nodes: {valid_nodes_in_community})")
        center = coords_array[0]
        radius = min_community_padding
        patch_to_add = mpatches.Circle(center, radius=radius, **patch_kwargs)

    return patch_to_add


def draw_traversal_arrows(
    ax: plt.Axes,
    edges: List[Tuple[int, int]],
    layout_coords: Dict[int, Tuple[float, float]],
    color: str,
    node_size: float,
    shrink_factor_rel: float = DEFAULT_ARROW_SHRINK_FACTOR_REL_TO_NODE_SIZE,
    lw: float = DEFAULT_ARROW_LW,
    mutation_scale: int = DEFAULT_ARROW_MUTATION_SCALE,
    connectionstyle: str = DEFAULT_ARROW_CONNECTION_STYLE,
) -> None:
    """Draws arrows on the plot for a given set of edges."""
    # Calculate absolute shrink based on node size (visual radius)
    # igraph uses diameter for vertex_size, matplotlib radius often assumed
    # Let's assume node_size is diameter. Radius is node_size / 2.
    # Shrink needs to be in *display* coordinates usually, but igraph layout is data coords.
    # Let's base shrink on data coordinates relative to typical node size scale.
    # Heuristic: Shrink based on a fraction of the visual node size.
    # If node_size is 35, radius is 17.5. Shrink factor of 15 was used.
    # shrink_abs = node_size * shrink_factor_rel # Adjust this logic as needed
    # Let's stick to the original hardcoded shrink factor, but make it a parameter
    arrow_shrink_factor = 15  # Keep original value, make parameter if needed later

    if not layout_coords:
        print("Warning: Layout coordinates are empty. Cannot draw arrows.")
        return

    for start_node, end_node in edges:
        if start_node in layout_coords and end_node in layout_coords:
            start_coords = np.array(layout_coords[start_node])
            end_coords = np.array(layout_coords[end_node])

            # Avoid drawing zero-length arrows if start/end are same point
            if np.linalg.norm(end_coords - start_coords) < 1e-6:
                print(
                    f"  Skipping zero-length {color} arrow: {start_node} -> {end_node}"
                )
                continue

            ax.annotate(
                "",
                xy=end_coords,
                xycoords="data",
                xytext=start_coords,
                textcoords="data",
                arrowprops=dict(
                    arrowstyle="->",
                    color=color,
                    lw=lw,
                    shrinkA=arrow_shrink_factor,  # Shrink start
                    shrinkB=arrow_shrink_factor,  # Shrink end
                    patchA=None,
                    patchB=None,
                    connectionstyle=connectionstyle,
                    mutation_scale=mutation_scale,
                ),
            )
        else:
            print(
                f"  Skipping {color} Arrow: Node(s) not in layout_coords "
                f"(Start: {start_node}, End: {end_node})"
            )



