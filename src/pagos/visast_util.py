import ast

import matplotlib.pyplot as plt
import networkx as nx
from visast.visualise import __plotGraph
from pint.util import UnitsContainer


def graph(aST: ast) -> None:
    """Builds a visualisation of the provided AST.

    Args:
        aST (AST): The abstract syntax tree.
    """
    GRAPH = nx.DiGraph()
    rootNodeID = "noRoot"
    edges = []
    labelDictionary = {}

    # Walk the tree, breadth-first, noting all edges.
    for node in ast.walk(aST):
        nodeID = str(node.__class__) + str(id(node))  # Unique name
        nodeLabel = str(node.__class__).split("ast.")[1].split("'>")[0]
        if nodeLabel == "Constant":
            nodeLabel += " " + str(node.value)
        elif nodeLabel == "FunctionDef":
            nodeLabel += " " + str(node.name)

        if hasattr(node, "units"):
            if isinstance(node.units, (str, UnitsContainer)):
                nodeLabel += f"\n{node.units!s}"
            elif isinstance(node.units, list):
                nodeLabel += "\n..."
            else:
                nodeLabel += "\nU"

        labelDictionary[nodeID] = nodeLabel

        if rootNodeID == "noRoot":
            rootNodeID = nodeID

        for child in ast.iter_child_nodes(node):
            childNodeID = str(child.__class__) + str(id(child))
            for edge in edges:
                if edge[1] == childNodeID:
                    childNodeID += str(1)  # IDs aren't unique.  Fix.

            # If child is at the bottom of the tree, it won't get walked.
            # Label it manually.
            if labelDictionary.get(childNodeID) is None:
                childLabel = str(child.__class__).split("t.")[1].split("'>")[0]
                if childLabel == "Constant":
                    childLabel += " " + str(child.value)

                if hasattr(child, "units"):
                    if not isinstance(child.units, (str, UnitsContainer)):
                        childLabel += "\nU"
                    elif isinstance(child.units, list):
                        childLabel += "\n..."
                    else:
                        childLabel += f"\n{child.units!s}"

                labelDictionary[childNodeID] = childLabel

                if (
                    (cl := childLabel.split("\n")[0]) == "Load"
                    or cl == "Store"
                    or cl == "Del"
                ):
                    if hasattr(node, "id"):
                        nodeLabel = str(node.id)
                        if hasattr(node, "units"):
                            if not isinstance(node.units, (str, UnitsContainer)):
                                nodeLabel += "\nU"
                            elif isinstance(node.units, list):
                                nodeLabel += "\n..."
                            else:
                                nodeLabel += f"\n{node.units!s}"
                        labelDictionary[nodeID] = nodeLabel

            GRAPH.add_edge(nodeID, childNodeID)
            edges.append([nodeID, childNodeID])
    __plotGraph(GRAPH, rootNodeID, labelDictionary)


def __colourNodes(labels: dict) -> list:
    """Private.  Colours important nodes in an AST.
    For python 3.9 support, this uses an if statement.  It would be more
    efficient in 3.10+ to use a match/case block.

    Args:
        labels(dict(str)): the labels for the AST.  Search these for features.

    Returns:
        list: the list of colours for nodes in the graph.
    """
    colourMap = []
    for label in labels:
        cleanLabel = label.split("ast.")[1].split("'>")[0]
        try:
            labelunit = labels[label].split("\n")[1]
        except IndexError:
            labelunit = None
        if labelunit == "U":
            colourMap.append("#ff0000")
        elif labelunit == "...":
            colourMap.append("#ffaa00")
        elif cleanLabel == "Module":
            colourMap.append("#b3ffb3")
        elif cleanLabel == "ClassDef":
            colourMap.append("#ffffb3")
        elif cleanLabel == "FunctionDef":
            colourMap.append("#ffb3ff")
        else:
            colourMap.append("#1f78b4")
    return colourMap


from visast import visualise

visualise.__colourNodes = __colourNodes
