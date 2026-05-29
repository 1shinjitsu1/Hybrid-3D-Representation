import bpy
import mathutils

print("\n=== OBJECT INFO ===")

for obj in bpy.data.objects:
    if obj.type == 'MESH':
        print(f"\nObject: {obj.name}")
        print("  Location:", tuple(obj.location))
        print("  Dimensions:", tuple(obj.dimensions))

        bbox_corners = [obj.matrix_world @ mathutils.Vector(corner) for corner in obj.bound_box]
        min_corner = [min([v[i] for v in bbox_corners]) for i in range(3)]
        max_corner = [max([v[i] for v in bbox_corners]) for i in range(3)]

        print("  BBox min:", min_corner)
        print("  BBox max:", max_corner)


print("\n=== MATERIAL INFO ===")

for mat in bpy.data.materials:
    if mat.use_nodes:
        print(f"\nMaterial: {mat.name}")
        for node in mat.node_tree.nodes:
            if node.type == 'BSDF_PRINCIPLED':
                print("  Principled BSDF:")
                print("    Base Color:", node.inputs['Base Color'].default_value)
                print("    Roughness:", node.inputs['Roughness'].default_value)
                print("    Specular:", node.inputs['Specular'].default_value)

            if node.type == 'HUE_SAT':
                print("  HSV Node:")
                print("    Hue:", node.inputs['Hue'].default_value)
                print("    Saturation:", node.inputs['Saturation'].default_value)
                print("    Value:", node.inputs['Value'].default_value)


print("\n=== DRIVERS ===")

for obj in bpy.data.objects:
    if obj.animation_data and obj.animation_data.drivers:
        print(f"\nObject with drivers: {obj.name}")
        for d in obj.animation_data.drivers:
            print("  Data path:", d.data_path)
            print("  Expression:", d.driver.expression)
