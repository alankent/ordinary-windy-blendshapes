import omni.ext
import omni.ui as ui
from pxr import Usd, Sdf, Gf, UsdGeom, UsdSkel


# Any class derived from `omni.ext.IExt` in top level module (defined in `python.modules` of `extension.toml`) will be
# instantiated when extension gets enabled and `on_startup(ext_id)` will be called. Later when extension gets disabled
# on_shutdown() is called.
class OrdinaryWindyBlendshapesExtension(omni.ext.IExt):
    # ext_id is current extension id. It can be used with extension manager to query additional information, like where
    # this extension is located on filesystem.
    def on_startup(self, ext_id):
        print("[ordinary.windy.blendshapes] ordinary windy blendshapes startup")

        self._window = ui.Window("Ordinary Windy Blendshapes", width=300, height=300)
        with self._window.frame:
            with ui.VStack():
                label = ui.Label("Instructions\n\n" +
                                 "- Create a new stage\n" +
                                 "- Click 'Create Skeleton'\n" +
                                 "- Drop your model under SkelRoot\n" +
                                 "- Click 'Add Blend Shapes'\n" +
                                 "- Save and reload the file (to flush the skeleton cache)")

                def on_create_skeleton():
                    self.create_skeleton()

                def on_add_blend_shapes():
                    self.add_blend_shapes()

                with ui.HStack():
                    ui.Button("Create Skeleton", clicked_fn=on_create_skeleton)
                    ui.Button("Add Blend Shapes", clicked_fn=on_add_blend_shapes)

    def on_shutdown(self):
        print("[ordinary.windy.blendshapes] ordinary windy blendshapes shutdown")

    def create_skeleton(self):
        ctx = omni.usd.get_context()
        stage: Usd.Stage = ctx.get_stage()

        root: Usd.Prim = stage.GetDefaultPrim()

        # Create a skeleton under which the user will have to add a reference to the model.
        skel_root: UsdSkel.Root = UsdSkel.Root.Define(stage, root.GetPath().AppendChild("SkelRoot"))

        skeleton: UsdSkel.Skeleton = UsdSkel.Skeleton.Define(stage, skel_root.GetPath().AppendChild("Skeleton"))
        UsdSkel.BindingAPI.Apply(skeleton.GetPrim())
        skeleton.CreateBindTransformsAttr().Set([])
        skeleton.CreateRestTransformsAttr().Set([])
        skeleton.CreateJointsAttr().Set([])
        skeleton.CreateJointNamesAttr().Set([])

        # Add a SkelAnimation referring to the blend shapes to simplify animation.
        no_wind_anim = self.add_skel_animation(stage, skeleton, "noWindAnimation", 0, 0)
        self.add_skel_animation(stage, skeleton, "eastWindAnimation", 1, 0)
        self.add_skel_animation(stage, skeleton, "southWindAnimation", 0, 1)

        # Point the skeleton to the no wind animation.
        skel_binding: UsdSkel.BindingAPI = UsdSkel.BindingAPI(skeleton)
        skel_binding.CreateAnimationSourceRel().SetTargets([no_wind_anim.GetPath()])

    def add_skel_animation(self, stage: Usd.Stage, skeleton: UsdSkel.Skeleton, animation_name, east_weight, south_weight):
        skel_animation: UsdSkel.Animation = UsdSkel.Animation.Define(stage, skeleton.GetPath().AppendChild(animation_name))
        skel_animation.CreateBlendShapesAttr().Set(["eastWindBlendShape", "southWindBlendShape"])
        skel_animation.CreateBlendShapeWeightsAttr().Set([east_weight, south_weight])
        skel_animation.CreateJointsAttr().Set([])
        skel_animation.CreateRotationsAttr().Set([])
        skel_animation.CreateScalesAttr().Set([])
        skel_animation.CreateTranslationsAttr().Set([])
        return skel_animation

    def add_blend_shapes(self):
        ctx = omni.usd.get_context()
        stage: Usd.Stage = ctx.get_stage()

        root: Usd.Prim = stage.GetDefaultPrim()

        skel_root = root.GetChild("SkelRoot")
        if not skel_root.IsValid():
            print("SkelRoot not found - did you create the skeleton first?")
            return
        skeleton = skel_root.GetChild("Skeleton")
        if not skeleton.IsValid():
            print("Skeleton not found - did you create the skeleton first?")
            return

        # Cannot use Traverse unfortunately, as it is not restricted to under a specific prim.
        #for prim in stage.Traverse():
        #   if prim.IsA(UsdGeom.Mesh):
        #       print("Mesh: " + prim.GetPath().pathString)
        self.look_for_meshes(stage, root, skeleton)

    def look_for_meshes(self, stage, prim, skeleton):
        if prim.IsA(UsdGeom.Mesh):
            self.add_blend_shapes_for_mesh(stage, prim, skeleton)
        else:
            for child_prim in prim.GetChildren():
                self.look_for_meshes(stage, child_prim, skeleton)

    def add_blend_shapes_for_mesh(self, stage: Usd.Stage, mesh: UsdGeom.Mesh, skeleton):
        # Work out which way is up for the model.
        up = "Y"
        units_resolve_attr = mesh.GetPrim().GetParent().GetAttribute("xformOp:rotateX:unitsResolve")
        if units_resolve_attr:
            units_resolve = units_resolve_attr.Get()
            if units_resolve == 0:
                pass
            elif units_resolve == -90:
                up = "Z"
            else:
                print("I don't know what up is!")

        # Create child blend shapes for +X (east) and +Z (south)
        east_blend_shape = self.add_blendshape_in_one_direction(stage, up, mesh, "eastWindBlendShape", 1, 0)
        south_blend_shape = self.add_blendshape_in_one_direction(stage, up, mesh, "southWindBlendShape", 0, 1)
        # TODO: Add a third blendshape for fluttering leaves

        # Add skel:blendShapes property to list the blendshape names.
        # https://openusd.org/dev/api/class_usd_skel_binding_a_p_i.html
        binding: UsdSkel.BindingAPI = UsdSkel.BindingAPI(mesh)
        binding.CreateBlendShapesAttr().Set(["eastWindBlendShape", "southWindBlendShape"])
        binding.CreateBlendShapeTargetsRel().SetTargets([east_blend_shape.GetPath(), south_blend_shape.GetPath()])
        UsdSkel.BindingAPI.Apply(mesh.GetPrim())

        binding.CreateSkeletonRel().SetTargets([skeleton.GetPath()])


    def add_blendshape_in_one_direction(self, stage: Usd.Stage, up, mesh: UsdGeom.Mesh, blend_shape_name, east_scale, south_scale):
        # Work out how many points in blendshape we need.
        # We specify all points (0..n), normal offsets are all zero. Point offsets are the most complex.
        #print(mesh.GetPath().pathString)
        #print(mesh.GetPropertyNames())
        #print(mesh.GetAttribute("points"))
        #print(mesh.GetAttribute("points").Get())
        #mesh_points = mesh.GetPointsAttr().Get()
        mesh_points = mesh.GetAttribute("points").Get()
        num_points = len(mesh_points)
        point_indices = range(0, num_points)
        normal_offsets = [(0, 0, 0) for i in point_indices]

        # To work out how far to bend the object, we need to know its height.
        height = 0
        offsets = []

        if up == "Y":
            for x, y, z in mesh_points:
                if y > height:
                    height = y

            for x, y, z in mesh_points:
                if y <= 0:
                    offsets.append((0, 0, 0))
                else:
                    delta = y # ((y / height) ** 2) * (height / 4)
                    offsets.append((delta * east_scale, 0, delta * south_scale))

        if up == "Z":
            for x, y, z in mesh_points:
                if z > height:
                    height = z

            for x, y, z in mesh_points:
                if z <= 0:
                    offsets.append((0, 0, 0))
                else:
                    delta = self.compute_delta(height, z)
                    offsets.append((delta * east_scale, delta * south_scale, 0))

        # Create the blendshape! https://openusd.org/dev/api/class_usd_skel_blend_shape.html
        blend_shape: UsdSkel.BlendShape = UsdSkel.BlendShape.Define(stage, mesh.GetPath().AppendChild(blend_shape_name))
        blend_shape.CreatePointIndicesAttr().Set(point_indices)
        blend_shape.CreateOffsetsAttr().Set(offsets)
        blend_shape.CreateNormalOffsetsAttr().Set(normal_offsets)

        return blend_shape

    def compute_delta(self, max, value):
        #return value
        return ((value / max) ** 2) * (max / 4)