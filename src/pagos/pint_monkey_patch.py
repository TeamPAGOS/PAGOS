# Monkey patching for Pint functionalities
from __future__ import annotations

from pint._typing import Magnitude
from pint.util import UnitsContainer, find_shortest_path

from collections import defaultdict, deque
from collections.abc import Hashable
from typing import TypeVar
TH = TypeVar("TH", bound=Hashable)
import pint.facets.context.registry as registry

from math import copysign

# this is the same as _convert in GenericContextRegistry, but modified to allow for conversions
# between compound units. For example, currently Pint cannot convert between A/B <-> C/B, even
# if A <-> C is defined in the context, because the dimension [B] is not in the transformation
# graph. 
def _convert_new(
        obj,
        value: Magnitude,
        src: UnitsContainer,
        dst: UnitsContainer,
        inplace: bool = False,
        **ctx_kwargs,
    ) -> Magnitude:
        """Convert value from some source to destination units.

        In addition to what is done by the PlainRegistry,
        converts between units with different dimensions by following
        transformation rules defined in the context.

        Parameters
        ----------
        value :
            value
        src : UnitsContainer
            source units.
        dst : UnitsContainer
            destination units.
        inplace :
             (Default value = False)
        **ctx_kwargs :
            keyword arguments for the context

        Returns
        -------
        callable
            converted value
        """
        # If there is an active context, we look for a path connecting source and
        # destination dimensionality. If it exists, we transform the source value
        # by applying sequentially each transformation of the path.
        if obj._active_ctx:
            src_dim = obj._get_dimensionality(src)
            dst_dim = obj._get_dimensionality(dst)

            # find_shortest_path will fail if units with a transformation within
            # a context are combined with units without a transformation. For
            # example in spectroscopic context:
            # Quantity(5, 'Hz/mm').to('nm/mm', 'sp')
            # would usually fail, because the mm is not contained in the
            # transformation paths. The following block removes common dimensions
            # to src_dim and dst_dim - in the example case, the common dimension
            # of 1 [length] is removed.
            intersect = src_dim.keys() & dst_dim.keys()
            to_remove = []
            while intersect:
                common_dim = intersect.pop()
                if src_dim[common_dim] == dst_dim[common_dim]:
                    to_remove.append(common_dim)
            src_dim, dst_dim = src_dim.remove(to_remove), dst_dim.remove(to_remove)

            # code for dealing with compound units
            ctx_subgraphs = split_graph_components(obj._active_ctx.graph)
            _src_dim, _dst_dim = dict(src_dim), dict(dst_dim)
            pairs = []


            # for each "base" dimension in source dimensions (i.e. without exponents)
            while _src_dim:
                base_sd = next(iter(_src_dim)) 
                # find subgraph containing base_sd
                for subgraph in ctx_subgraphs.values(): # the graph should never be empty, so this should never fail

                    # make sets of nodes with incoming and outgoing edges, and of the base dimensions in the subgraph
                    subgraph_in, subgraph_out, subgraph_base_dims = set(), set(), set()
                    for node, targets in subgraph.items():
                        subgraph_in.add(node)
                        subgraph_base_dims.add(next(iter(node)))
                        for target in targets:
                            subgraph_out.add(target)
                            subgraph_base_dims.add(next(iter(target)))
                    
                    

                    if base_sd in subgraph_base_dims:
                        # find the highest exponent of base_sd that is in the subgraph
                        exp_src = _src_dim[base_sd]
                        sign_src = int(copysign(1, _src_dim[base_sd]))
                        while exp_src != 0:
                            if UnitsContainer({base_sd:exp_src}) in subgraph_in:
                                break
                            # if not, reduce exponent by 1 and try again
                            else:
                                exp_src -= sign_src
                        else:
                            # continue to next subgraph if the dimension isn't in this subgraph with this sign
                            continue

                        # do the same for destination dimensions
                        # loop through all candidate destination base dimensions - must come from same subgraph
                        for base_dd in subgraph_base_dims:
                            if base_dd != base_sd and base_dd in _dst_dim:
                                # find the highest exponent of base_sd that is in the subgraph
                                exp_dst = _dst_dim[base_dd]
                                sign_dst = int(copysign(1, _dst_dim[base_dd]))
                                while exp_dst != 0:
                                    if UnitsContainer({base_dd:exp_dst}) in subgraph_out:
                                        break
                                    # if not, reduce exponent by 1 and try again
                                    else:
                                        exp_dst -= sign_dst
                                else:
                                    # continue to next base_dd if the dimension isn't in this subgraph with this sign
                                    continue

                                # add found pair of units and exponents to pairs
                                pairs.append((UnitsContainer({base_sd:exp_src}), UnitsContainer({base_dd:exp_dst})))
                                # remove the handled dimensions from _src_dim and _dst_dim
                                _src_dim[base_sd] -= exp_src
                                _dst_dim[base_dd] -= exp_dst
                                # delete dimensions if the exponent is now zero
                                if _src_dim[base_sd] == 0:
                                    del _src_dim[base_sd]
                                if _dst_dim[base_dd] == 0:
                                    del _dst_dim[base_dd]
                                break
                        else:
                            continue
                        break
                    else:
                        continue
                else:
                    # put None in pairs if the source unit is not in any subgraph
                    pairs.append((None, None))
                    break


            # paths for each pair of source and destination dimension
            paths = [find_shortest_path(obj._active_ctx.graph, s, d) for s, d in pairs]
            src = obj.Quantity(value, src)
            for path in paths:
                if not path:
                    break
                else:
                    for a, b in zip(path[:-1], path[1:]):
                        src = obj._active_ctx.transform(a, b, obj, src, **ctx_kwargs)
            
            value, src = src._magnitude, src._units

        return super(registry.GenericContextRegistry, obj)._convert(value, src, dst, inplace, **ctx_kwargs)

# helper function that splits a disconnected graph into its connected component subgraphs
def split_graph_components(graph: dict[TH, set[TH]]) -> dict[dict[TH, set[TH]]]: 
    # Convert to undirected graph for component detection
    undirected = defaultdict(set)
    for node, neighbors in graph.items():
        for neighbor in neighbors:
            undirected[node].add(neighbor)
            undirected[neighbor].add(node)

    # Find connected components using BFS
    visited = set()
    components = {}
    component_id = 1

    for node in graph:
        if node not in visited:
            queue = deque([node])
            component_nodes = set()
            visited.add(node)

            while queue:
                current = queue.popleft()
                component_nodes.add(current)
                for neighbor in undirected[current]:
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append(neighbor)

            # Build the component subgraph using original graph directions
            component_graph = {
                n: graph[n] for n in component_nodes if n in graph
            }
            components[component_id] = component_graph
            component_id += 1

    return components


"""
MONKEY PATCHES TO PINT
"""
from pagos.pint_monkey_patch import _convert_new
import pint.facets.context.registry as registry
registry.GenericContextRegistry._convert = _convert_new