from compas_assembly.algorithms import assembly_interfaces
from compas_assembly.datastructures import Assembly
from compas_assembly.geometry import Arch
from compas_model.elements import BlockElement
from compas_model.interactions import Interaction
from compas_model.model import Model


class DefaultInteraction(Interaction):
    pass


class CompoundInteraction(Interaction):
    pass


arch = Arch(rise=3, span=10, thickness=0.3, depth=0.5, n=30)
assembly = Assembly.from_template(arch)

assembly_interfaces(assembly, nmax=7, tmax=1e-3, amin=1e-2)

model = Model()

node_element = {}

for node in assembly.graph.nodes():
    block = assembly.node_block(node)
    element = BlockElement(shape=block)
    model.add_element(element)
    node_element[node] = element

for index, edge in enumerate(assembly.graph.edges()):
    interfaces = assembly.edge_interfaces(edge)
    interface = interfaces[0]
    a = node_element[edge[0]]
    b = node_element[edge[1]]

    if index % 3:
        model.add_interaction(a, b, interaction=CompoundInteraction())
    else:
        model.add_interaction(a, b, interaction=DefaultInteraction())

components = model.elements_connected_by(CompoundInteraction)

print(len(model.elementlist))
print(len(components))
for component in components:
    print(component)
