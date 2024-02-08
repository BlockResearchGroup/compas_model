from compas.geometry import Translation

xform = Translation.from_vector([0, 0, 0.1])
print(xform[0, 0])