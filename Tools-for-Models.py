import bpy
import bpy.types
import bpy.props
import bmesh
import traceback

_DEBUG = False

bl_info = {
    'version': (0, 6),
    'blender': (2, 79, 0),
    'author': "Leland Green",
    'name': "Tools for Models",
    'description': """Written primarily to help automate preparation of models created in Masterpiece VR.

I believe this add-on will now perform all of the recommended steps from this forum post by one of the Masterpiece VR 
developers: http://forum.masterpiecevr.com/t/how-to-uv-unwrap-an-exported-mpvr-model-in-blender/135

I'm releasing this as open source under the MIT license. 

You should have received a copy of the MIT license with this software. 
If you *did not*, please see my original repository here: 
https://github.com/lelandg/Tools-for-Models
""", 'category': "TOOLS"}


def report_exception(obj: object, error_from: object):
    """Formats exception for error window in a manner suitable for end-users.
    Note: obj MUST contain the ".report()" macro in Blender, so call from e.g. a panel.
    """
    formatted_lines = traceback.format_exc().splitlines()
    lines = []
    for line in formatted_lines:
        if len(line):  # Should always be True.
            msg = line.split(',')[2:]
            if _DEBUG:
                obj.report({'INFO'}, 'DEBUG -- report_exception() msg = "%s", line = "%s":' % (msg, line))
            if len(msg[0:]):
                lines.append(msg[0])
            else:
                lines.append(line)

    obj.report({'ERROR'}, 'Error%s from %s:' % ('s' if len(lines) > 1 else '', error_from))
    for s in lines:
        obj.report({'ERROR'}, '%s' % (s,))


# Removes all decimate modifiers and returns the total number of meshes that were modified.
def remove_all_decimate_modifiers(obj):
    ntotal = 0
    for m in obj.modifiers:
        if m.type == "DECIMATE":
            obj.modifiers.remove(modifier=m)
            ntotal += 1
    return ntotal


def get_symmetry_item(obj):
    return obj['decimate_symmetry_axis']


def set_symmetry_item(obj, value):
    obj['decimate_symmetry_axis'] = value


def __init_data(scn):
    """Register data types and initialize values stored in each scene, if not already present."""
    keys = scn.keys()

    bpy.types.Scene.min_distance = bpy.props.FloatProperty(
        name='min_distance',
        description='Minimum distance between elements to merge.',
        default=0.005,
        min=0,
        max=1,
        precision=3)
    if 'min_distance' not in keys:
        scn['min_distance'] = 0.005

    bpy.types.Scene.decimate_triangulate = bpy.props.BoolProperty(
        name='decimate_triangulate',
        description='Triangulate: Keep triangulated faces resulting from decimation (collapse only).',
        default=False)
    if 'decimate_triangulate' not in keys:
        scn['decimate_triangulate'] = False

    bpy.types.Scene.decimate_symmetry = bpy.props.BoolProperty(
        name='decimate_symmetry',
        description='Symmetry: Maintain symmetry on an axis.',
        default=False)
    if 'decimate_symmetry' not in keys:
        scn['decimate_symmetry'] = False

    bpy.types.Scene.symmetry_axis_items = [('1', 'X', '0'),
                                           ('2', 'Y', '0'),
                                           ('3', 'Z', '0')]
    bpy.types.Scene.decimate_symmetry_axis = bpy.props.EnumProperty(
        items=bpy.types.Scene.symmetry_axis_items,
        name='decimate_symmetry_axis',
        default='1',
        description='Axis of Symmetry',
        get=get_symmetry_item,
        set=set_symmetry_item
    )
    if 'symmetry_axis_items' not in keys:
        scn['symmetry_axis_items'] = '1'

    # Properties for Smart UV unwrap
    bpy.types.Scene.angle_limit = bpy.props.FloatProperty(
        name='angle_limit',
        description='Angle Limit: Lower for more projection groups, higher for less distortion',
        default=33.00,
        min=1,
        max=89)
    if 'angle_limit' not in keys:
        scn['angle_limit'] = 33.00

    bpy.types.Scene.island_margin = bpy.props.FloatProperty(
        name='island_margin',
        description='Island Margin: Margin to reduce bleed from adjacent islands.',
        default=0.40,
        min=0,
        max=1)
    if 'island_margin' not in keys:
        scn['island_margin'] = 0.40

    bpy.types.Scene.area_weight = bpy.props.FloatProperty(
        name='area_weight',
        description='Area Weight: Weight projections vector by faces with larger areas.',
        default=0,
        min=0,
        max=1,
        precision=3)
    if 'area_weight' not in keys:
        scn['area_weight'] = 0.0

    bpy.types.Scene.correct_aspect = bpy.props.BoolProperty(
        name='correct_aspect',
        description='Correct Aspect: Map UVs taking image aspect ratio into account.',
        default=True)
    if 'correct_aspect' not in keys:
        scn['correct_aspect'] = True

    bpy.types.Scene.stretch_to_uv_bounds = bpy.props.BoolProperty(
        name='stretch_to_uv_bounds',
        description='Stretch to UV Bounds: Stretch the final output to texture bounds.',
        default=True)
    if 'stretch_to_uv_bounds' not in keys:
        scn['stretch_to_uv_bounds'] = True

    bpy.types.Scene.delete_uv_maps = bpy.props.BoolProperty(
        name='delete_uv_maps',
        description='Delete UVs: Remove ALL existing UVMaps (before running UV Smart Project).',
        default=False)
    if 'delete_uv_maps' not in keys:
        scn['delete_uv_maps'] = False

    return


__init_data(bpy.context.scene)


class SYMMETRY_LIST_OT_Menu(bpy.types.Operator):
    bl_idname = "symmetry_axis.menu"
    bl_description = "Select axis for symmetry"
    bl_label = "Symmetry"

    @staticmethod
    def get_items(context):
        return context.scene.symmetry_axis_items

    axisList = bpy.props.EnumProperty(
        items=get_items, name="Symmetry", description="Symmetry axis choices")

    def execute(self, context):
        self.report({'INFO'}, 'symmetry_axis.menu.execute(context = "%s")' % (str(context),))
        bpy.props.selectedStuff = [n for i, n in enumerate(context.scene.symmetry_axis_items)
                                   if n[0] == self.axisList][0]
        return {'FINISHED'}


class VIEW3D_PT_tools_ToolsForModels(bpy.types.Panel):
    """Creates a Panel in the Object properties window on the Tools tab"""
    bl_label = "Tools for Models"
    bl_idname = "OBJECT_PT_grd_panel"
    bl_space_type = 'VIEW_3D'
    bl_category = "Tools"
    bl_region_type = 'TOOLS'
    bl_icon = 'WORLD_DATA'

    # bl_context = "scene"

    def draw(self, context):
        layout = self.layout

        row = layout.row(align=True)
        row.alignment = 'EXPAND'
        row.label(text='', icon='WORLD_DATA')
        col = row.column()
        subrow = col.row(align=True)

        subrow.label(text='This entire panel operates on all objects')
        subrow = col.row(align=True)
        subrow.alignment = 'EXPAND'
        subrow.label(text='globally, whether they are selected or not.')
        scene = context.scene

        layout.row()
        layout.prop(scene, 'min_distance', 'Minimum Distance', 'Minimum Distance', slider=True)

        layout.row()
        layout.operator('grd_panel.remove_doubles_global')
        row = layout.row()
        row.label(text='Decimate:', icon='MOD_DECIM')
        layout.prop(scene, 'decimate_ratio', 'Ratio', slider=True)

        row = layout.row(align=True)
        row.alignment = 'EXPAND'
        row.prop(scene, 'decimate_triangulate', 'Triangulate')

        # Symmetry rows
        row = layout.row(align=True)
        row.alignment = 'EXPAND'
        split = row.split(percentage=0.5)
        col = split.column(align=True)
        col.alignment = 'LEFT'
        col.prop(scene, 'decimate_symmetry', 'Symmetry')
        col = split.column(align=True)
        col.alignment = 'LEFT'
        col.prop(scene, 'decimate_symmetry_axis', 'Axis')

        # Decimate buttons
        layout.row()
        layout.operator('grd_panel.decimate_globally')

        layout.row()
        layout.operator('grd_panel.undecimate_globally')

        # Smart UV Project stuff
        layout.row()
        layout.prop(scene, 'angle_limit', 'Angle Limit', 'Angle Limit', slider=True)

        layout.row()
        layout.prop(scene, 'island_margin', 'Margin', 'Margin', slider=True)

        layout.row()
        layout.prop(scene, 'area_weight', 'Area Weight', 'Area Weight', slider=True)

        layout.row()
        layout.prop(scene, 'correct_aspect', 'Correct Aspect')

        layout.row()
        layout.prop(scene, 'stretch_to_uv_bounds', 'Stretch to UV Bounds')

        layout.row()
        layout.prop(scene, 'delete_uv_maps', 'Delete UV Maps')

        layout.row()
        layout.operator('grd_panel.smart_uv_project')

        # Debug stuff
        global _DEBUG
        if _DEBUG:
            layout.row()
            layout.operator('grd_panel.my_debug')


class OBJECT_OT_SmartUVProject(bpy.types.Operator):
    """Smart UV project."""
    bl_idname = 'grd_panel.smart_uv_project'
    bl_label = 'Smart UV Project'

    def execute(self, context):
        restore_obj = bpy.context.scene.objects.active
        ncount = 0
        ntotal = 0
        # noinspection PyBroadException
        try:
            self.report({'INFO'}, 'Smart UV Project...')
            scene = context.scene

            area_weight = scene['area_weight']
            correct_aspect = scene['correct_aspect']
            stretch_to_uv_bounds = scene['stretch_to_uv_bounds']
            angle_limit = scene['angle_limit']
            island_margin = scene['island_margin']
            delete_uv_maps = scene['delete_uv_maps']

            if _DEBUG:
                self.report({'INFO'},
                            'angle_limit = %s, island_margin = %s, area_weight = %s, correct_aspect = %s, '
                            'stretch_to_uv_bounds = %s, delete_uv_maps = %s' % (
                                str(angle_limit), str(island_margin), str(area_weight), str(correct_aspect),
                                str(stretch_to_uv_bounds), str(delete_uv_maps)))

            found_any = False
            for obj in bpy.data.objects:
                if obj.type == "MESH":
                    ntotal += 1
                    if delete_uv_maps:
                        if len(obj.data.uv_textures):
                            if _DEBUG:
                                self.report({'INFO'}, 'Removing UVMap from %s' % (obj.name,))
                            bpy.context.scene.objects.active = obj
                            while len(obj.data.uv_textures):
                                bpy.ops.mesh.uv_texture_remove()

                    if not len(obj.data.uv_layers):
                        ncount += 1
                        # bpy.data.objects[obj.name].select = True
                        obj.select = True
                        found_any = True
                        if _DEBUG:
                            self.report({'INFO'}, 'Selected object %s' % (obj.name,))
                    else:
                        self.report({'INFO'},
                                    'obj %s has existing data.uv_layers: %s' % (obj.name, obj.data.uv_layers[0]))
                        obj.select = False
                        # bpy.data.objects[obj.name].select = False
                else:
                    obj.select = False

            if found_any:
                self.report({'INFO'}, 'Running Smart UV Project on %d meshes...' % (ncount,))
                bpy.ops.uv.smart_project(angle_limit=angle_limit, island_margin=island_margin,
                                         user_area_weight=area_weight,
                                         use_aspect=correct_aspect, stretch_to_bounds=stretch_to_uv_bounds)

                self.report({'INFO'},
                            'Smart UV Project performed on %d of %d meshes' % (ncount, ntotal))
            else:
                self.report({'INFO'},
                            'UVMap found on all layers. Please tick the "Remove UVs" box to remove all existing UV '
                            'maps.')
        except:
            if ncount:
                self.report({'INFO'},
                            'Smart UV Project performed on %d of %d meshes' % (ncount, ntotal))
            report_exception(self, 'Smart UV Project')

        if restore_obj:
            bpy.context.scene.objects.active = restore_obj
        return {'FINISHED'}


class OBJECT_OT_UnDecimateGloballyButton(bpy.types.Operator):
    """UnDecimate all meshes globally, aborting on error and reporting it in the console."""
    bl_idname = 'grd_panel.undecimate_globally'
    bl_label = 'Undecimate Meshes'

    # noinspection PyUnusedLocal
    def execute(self, context):
        ncount = 0
        ntotal = 0
        try:
            object_list = bpy.data.objects
            for obj in object_list:
                if obj.type == "MESH":
                    self.report({'INFO'}, 'Removing decimate modifier %s' % (str(obj),))
                    ncount += remove_all_decimate_modifiers(obj)
                    ntotal += 1

            self.report({'INFO'},
                        'Undecimated %d of %d meshes' % (ncount, ntotal))
        except:
            self.report({'ERROR'}, '%s' % (traceback.print_exc(),))
            self.report({'ERROR'},
                        'Abort after %d meshes -- see Info window for details. (Are you in Edit mode?)' % (
                            ncount,))

        return {'FINISHED'}


class OBJECT_OT_DecimateGloballyButton(bpy.types.Operator):
    """Decimate all meshes globally, aborting on error and reporting it in the console."""
    bl_idname = 'grd_panel.decimate_globally'
    bl_label = 'Decimate Meshes'

    def execute(self, context):
        ncount = 0
        try:
            scene = context.scene
            ratio = scene['decimate_ratio']
            triangulate = scene['decimate_triangulate']
            symmetry = scene['decimate_symmetry']
            # self.report({'INFO'}, 'symmetry = %s %s' % (str(symmetry), type(symmetry)))
            symmetry_axis = 'X'
            if symmetry:
                symmetry_axis = bpy.types.Scene.symmetry_axis_items[scene['decimate_symmetry_axis']][1]
            # self.report({'INFO'}, 'symmetry_axis = "%s" %s' % (str(symmetry_axis), type(symmetry_axis)))

            object_list = bpy.data.objects
            for obj in object_list:
                self.report({'INFO'}, 'Checking %s' % (str(obj),))
                if obj.type == "MESH":
                    self.report({'INFO'}, 'Decimating %s' % (str(obj),))
                    remove_all_decimate_modifiers(obj)
                    self.report({'INFO'}, '  Removed doubles')
                    modifier = obj.modifiers.new("Decimate", type='DECIMATE')
                    modifier.decimate_type = 'COLLAPSE'
                    modifier.ratio = ratio
                    modifier.use_collapse_triangulate = triangulate
                    modifier.use_symmetry = symmetry
                    if symmetry:
                        modifier.symmetry_axis = symmetry_axis

                    ncount += 1
                    self.report({'INFO'}, '  Finished mesh!')

            context.scene.update()
            self.report({'INFO'},
                        'Finished decimating %d meshes)' % (ncount,))
        except:
            self.report({'ERROR'}, '%s' % (traceback.print_exc(),))
            self.report({'ERROR'},
                        'Abort after %d meshes -- see Info window for details.' % (
                            ncount,))

        return {'FINISHED'}


class OBJECT_OT_GlobalRemoveDoublesButton(bpy.types.Operator):
    bl_idname = 'grd_panel.remove_doubles_global'
    bl_label = 'Remove Doubles'

    def execute(self, context):
        ncount = 0
        mesh_count = len(bpy.data.meshes)
        total_verts = 0
        total_verts_removed = 0
        try:
            scene = context.scene

            bm = bmesh.new()
            min_distance = scene['min_distance']

            for m in bpy.data.meshes:
                self.report({'INFO'}, 'Processing %s' % (str(m),))
                bm.from_mesh(m)
                len1 = len(bm.verts)
                total_verts += len1
                self.report({'INFO'}, 'Processing %s: %d verts' % (str(m), len1))
                bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=min_distance)
                len2 = len(bm.verts)
                num_removed = len1 - len2
                total_verts_removed += num_removed
                self.report({'INFO'}, 'Processed %s: removed %d of %d verts' % (str(m), num_removed, len1))
                bm.to_mesh(m)
                m.update()
                bm.clear()
                ncount += 1

            bm.free()
            self.report({'INFO'},
                        'Finished %d meshes: Removed %d of %d verts)' % (mesh_count, total_verts_removed, total_verts))
        except:
            self.report({'ERROR'}, '%s' % (traceback.print_exc(),))
            self.report({'ERROR'},
                        'Abort after %d of %d meshes -- see Info window for details. (Are you in Edit mode?): Removed '
                        '%d of %d verts)' % (ncount, mesh_count, total_verts_removed, total_verts))

        return {'FINISHED'}


class OBJECT_OT_GlobalDebug(bpy.types.Operator):
    bl_idname = 'grd_panel.my_debug'
    bl_label = 'Debug'

    def report_info(self, msg):
        self.report({'INFO'}, msg)

    def execute(self, context):
        self.report_info('Debug:')
        scene = context.scene
        self.report({'INFO'}, 'scene.keys = %s' % (scene.keys(),))
        # Your debug stuff here. E.g.:
        # self.report({'INFO'}, 'scene["min_distance"] = %s' % (scene['min_distance'],))

        return {'FINISHED'}


def register():
    bpy.utils.register_module(__name__)


def unregister():
    bpy.utils.unregister_module(__name__)


if __name__ == "__main__":
    register()
