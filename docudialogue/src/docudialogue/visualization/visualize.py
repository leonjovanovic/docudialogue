from docudialogue.graphs.triplet_handler import TripletGraph
import igraph as ig
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from typing import List, Tuple, Optional

from docudialogue.visualization.visualization_utils import calculate_community_patch, draw_traversal_arrows
from docudialogue.visualization.graph_plot_data_utils import ensure_node_labels, extract_communities_from_pipeline, prepare_traversal_arrows

def plot_graph_with_communities_and_traversal(
    graph: ig.Graph,
    communities: List[List[int]],
    traversal_path: List[int],
    parent_nodes: List[Optional[int]],
    layout_algorithm: str = "fr",
    figsize: Tuple[int, int] = (16, 16),
    vertex_node_size: int = 35,
    vertex_label_size: int = 15,
    default_node_color: str = "lightblue",
    default_edge_color: str = "lightgrey",
    edge_width: float = 0.5,
    community_cmap: str = "tab20",
    plot_title: str = "Graph Traversal with Community Highlighting",
    red_arrow_color: str = "red",
    blue_arrow_color: str = "blue",
    show_plot: bool = True,
    ax: Optional[plt.Axes] = None,  # Allow plotting on existing axes
) -> Tuple[plt.Figure, plt.Axes]:
    """
    Plots a graph, highlights communities with shapes, and shows traversal path.

    Args:
        graph: The igraph.Graph object.
        communities: List of lists, each inner list contains node IDs of a community.
        traversal_path: List of node indices in traversal order.
        parent_nodes: List of parent node indices corresponding to traversal_path.
        layout_algorithm: Name of the igraph layout algorithm to use.
        figsize: Size of the matplotlib figure.
        vertex_node_size: Size (diameter) of the vertex nodes.
        vertex_label_size: Font size for vertex labels.
        default_node_color: Default color for nodes.
        default_edge_color: Default color for edges.
        edge_width: Width of the graph edges.
        community_cmap: Matplotlib colormap name for communities.
        plot_title: Title for the plot.
        red_arrow_color: Color for parent->current arrows.
        blue_arrow_color: Color for previous->parent arrows.
        show_plot: Whether to call plt.show() at the end.
        ax: An optional existing matplotlib Axes object to plot on.

    Returns:
        Tuple containing the matplotlib Figure and Axes objects.
    """

    ensure_node_labels(graph)  # Ensure labels exist

    # --- Basic Graph Setup ---
    graph.vs["color"] = default_node_color
    graph.es["color"] = default_edge_color
    graph.vs["size"] = vertex_node_size  # Set size for layout/plotting consistency

    print(f"Graph has {graph.vcount()} vertices.")
    print(f"Starting node: {traversal_path[0] if traversal_path else 'N/A'}")

    # --- Layout Calculation ---
    print(f"Calculating layout using '{layout_algorithm}'...")
    layout = graph.layout(layout_algorithm)
    layout_coords = {i: layout[i] for i in range(graph.vcount())}
    print("Layout calculation complete.")

    # --- Plotting Setup ---
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
    else:
        fig = ax.get_figure()  # Get figure from existing axes

    plot_visual_style = {
        "vertex_label": graph.vs["label"],
        "vertex_color": graph.vs["color"],
        "vertex_size": graph.vs["size"],
        "vertex_label_color": "black",
        "vertex_label_size": vertex_label_size,
        "edge_color": graph.es["color"],
        "edge_width": edge_width,
        "layout": layout,
        "target": ax,
    }
    print("Plotting base graph...")
    ig.plot(graph, **plot_visual_style)
    print("Base graph plotted.")

    # --- Community Highlighting ---
    print("\nDrawing community polygons:")
    if communities:
        num_communities = len(communities)
        cmap = plt.cm.get_cmap(community_cmap, num_communities)
        community_colors = [mcolors.to_rgba(cmap(i)) for i in range(num_communities)]

        for i, community_nodes in enumerate(communities):
            patch = calculate_community_patch(
                community_nodes=community_nodes,
                layout_coords=layout_coords,
                graph_vcount=graph.vcount(),
                color_rgba=community_colors[i % len(community_colors)],
                # Pass other parameters if customization is needed
            )
            if patch:
                ax.add_patch(patch)
    else:
        print("No communities provided to highlight.")

    # --- Arrow Preparation and Drawing ---
    print("\nPreparing traversal arrows:")
    red_arrow_edges, blue_arrow_edges = prepare_traversal_arrows(
        traversal_path, parent_nodes, graph
    )

    print("Drawing traversal arrows:")
    # Draw RED arrows (Parent -> Current)
    draw_traversal_arrows(
        ax=ax,
        edges=red_arrow_edges,
        layout_coords=layout_coords,
        color=red_arrow_color,
        node_size=vertex_node_size,  # Pass node size for potential scaling
    )
    # Draw BLUE arrows (Previous -> Parent)
    draw_traversal_arrows(
        ax=ax,
        edges=blue_arrow_edges,
        layout_coords=layout_coords,
        color=blue_arrow_color,
        node_size=vertex_node_size,
    )
    print("Arrow drawing complete.")

    # --- Final Plot Adjustments ---
    title = f"{plot_title}\n(Red: Parent->Cur, Blue: Prev->Parent)"
    ax.set_title(title)
    ax.set_xticks([])  # Turn off ticks and labels
    ax.set_yticks([])
    ax.spines["top"].set_visible(False)  # Remove spines
    ax.spines["right"].set_visible(False)
    ax.spines["bottom"].set_visible(False)
    ax.spines["left"].set_visible(False)
    # plt.axis('off') # Alternative way to hide axes and spines

    fig.tight_layout()

    if show_plot:
        plt.show()

    return fig, ax

def visualize(triplet_graph: TripletGraph) -> None:
    """
    Main function to visualize the graph with communities and traversal paths.
    """

    graph_to_plot = triplet_graph._graph
    traversal_path_data = triplet_graph.global_traversal
    parent_nodes_data = triplet_graph.global_traversal_parents
    extracted_communities = extract_communities_from_pipeline(triplet_graph)

    if graph_to_plot and extracted_communities is not None:
        fig, ax = plot_graph_with_communities_and_traversal(
            graph=graph_to_plot,
            communities=extracted_communities,
            traversal_path=traversal_path_data,
            parent_nodes=parent_nodes_data,
            layout_algorithm="fr",  # Or "kk", "circle", "rt", "fr" etc.
            figsize=(14, 14),
            vertex_node_size=40,
            vertex_label_size=12,
            plot_title="Krackhardt Kite Graph Traversal & Communities"
        )
    else:
        print("Could not plot graph due to missing data.")