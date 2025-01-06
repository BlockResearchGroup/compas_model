from compas_model.interactions import ContactInterface
from compas_model.models import Model


def cra_penalty_solve(
    model: Model,
    mu: float = 0.84,
    density: float = 1.0,
    d_bnd: float = 0.001,
    eps: float = 0.0001,
    verbose: bool = False,
    timer: bool = False,
):
    try:
        from compas_cra.equilibrium import cra_penalty_solve as _cra_penalty_solve

        from compas_assembly.datastructures import Assembly
        from compas_assembly.datastructures import Block
    except ImportError:
        raise ImportError("compas_cra, compas_assembly is required for this functionality. Please install it via conda.")

    assembly = Assembly()

    element_block = {}

    for element in model.elements():
        block: Block = element.modelgeometry.copy(cls=Block)
        x, y, z = block.centroid()
        node = assembly.add_block(block, x=x, y=y, z=z, is_support=element.is_support)
        element_block[element.graphnode] = node

    for edge in model.graph.edges():
        interactions: list[ContactInterface] = model.graph.edge_interactions(edge)
        u = element_block[edge[0]]
        v = element_block[edge[1]]
        assembly.graph.add_edge(u, v, interfaces=interactions)

    _cra_penalty_solve(assembly, mu=mu, density=density, d_bnd=d_bnd, eps=eps, verbose=verbose, timer=timer)
