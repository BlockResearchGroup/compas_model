import compas.plugins


@compas.plugins.plugin(category="install")
def installable_rhino_packages():
    return ["compas_model"]  # add all other dependencies that are needed and work in rhino
