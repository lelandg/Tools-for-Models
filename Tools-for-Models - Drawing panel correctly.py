import bpy
import bpy.types
from bpy.props import *
import bmesh
import traceback

_DEBUG = False

bl_info = {
    'version': (0, 1),
    'blender': (2, 79, 0),
    'author': "Leland Green",
    'name': "Tools for Models",
    'description': """Written to help automate preparation of models created in Masterpiece VR.

This add-on does (optionally) all of the recommended steps from this forum post by one of the Masterpiece VR developers:

http://forum.masterpiecevr.com/t/how-to-uv-unwrap-an-exported-mpvr-model-in-blender/135

However, I believe this add-on will be generally useful for many different situations. Besides that there 
is a good chance that I will add more features over time.
 
Therefore, bequeathing to the public, I'm also releasing this as open source under the MIT license. 

You should have received a copy of the MIT license with this software. 
If you *did not*, please see my original repository here: 
https://github.com/lelandg/Tools-for-Models
""", 'category': "TOOLS"}

#numberOfIteration=2
#decimateRatio=0.3
#modifierName='DecimateMod'

##Cleans all decimate modifiers
def removeAllDecimateModifiers(obj):
    ntotal = 0
    for m in obj.modifiers:
        if(m.type=="DECIMATE"):
            obj.modifiers.remove(modifier=m)
            ntotal += 1
    return ntotal

def initSceneProperties(scn):
    """Register data types and initialize values stored in each scene, if not already present."""
    bpy.types.Scene.min_distance = FloatProperty(
        name = "min_distance", 
        description = "Minimum Distance",
        default = 0.005,
        min = 0,
        max = 1,
        precision = 3)
    if 'min_distance' not in scn.keys():
        scn['min_distance'] = 0.005

    bpy.types.Scene.decimate_ratio = FloatProperty(
        name = "decimate_ratio",
        description = "Ratio",
        default = 0.1,
        min = 0,
        max = 1)
    if 'decimate_ratio' not in scn.keys():
        scn['decimate_ratio'] = 0.1

    bpy.types.Scene.decimate_triangulate = BoolProperty(
        name = "decimate_triangulate",
        description = "Triangulate",
        default = False)
    if 'decimate_triangulate' not in scn.keys():
        scn['decimate_triangulate'] = False

    bpy.types.Scene.decimate_symmetry = BoolProperty(
        name = "decimate_symmetry",
        description = "Symmetry",
        default = False)
    if 'decimate_symmetry' not in scn.keys():
        scn['decimate_symmetry'] = False

    bpy.types.Scene.symmetry_axis_items =  [\
        ("1","X","0"),\
        ("2","Y","0"),\
        ("3","Z","0")]

    symmetry_axis = '1'
    if 'symmetry_axis' in scn.keys():
        symmetry_axis = scn['symmetry_axis']

    #        items, identifier, name, description, default...
    bpy.types.Scene.decimate_symmetry_axis = EnumProperty(
         items = bpy.types.Scene.symmetry_axis_items,
         name='decimate_symmetry_axis',
         default='1',
         description='Axis of Symmetry',
    )

    return

initSceneProperties(bpy.context.scene)

class SYMMETRY_LIST_OT_Menu(bpy.types.Operator):
    bl_idname = "symmetry_axis.menu"
    bl_description = "Select axis for symmetry"
    bl_label = "Symmetry"

    def get_items(self, context):
        return context.scene.symmetry_axis_items

    axisList = bpy.props.EnumProperty(
        items = get_items, name = "Symmetry", description = "Symmetry axis choices")

    def execute(self, context):
        self.report({'INFO'}, 'symmetry_axis.menu.execute(context = "%s")' % (str(context),))
        bpy.props.selectedStuff = [n for i, n in enumerate(context.scene.symmetry_axis_items)\
            if n[0] == self.axisList][0]
        return{'FINISHED'}


class VIEW3D_PT_tools_ToolsForModels(bpy.types.Panel):
    """Creates a Panel in the Object properties window on the Tools tab"""
    bl_label = "Tools for Models"
    bl_idname = "OBJECT_PT_grd_panel"
    bl_space_type = 'VIEW_3D'
    bl_category = "Tools"
    bl_region_type = 'TOOLS'
    bl_icon = 'WORLD_DATA'
    #bl_context = "scene"

    def draw(self, context):
        layout = self.layout

        row = layout.row(align=True)
        row.alignment = 'EXPAND'
        row.label(text = '', icon='WORLD_DATA')
        col = row.column()
        subrow = col.row(align=True)

        subrow.label(text='This entire panel operates on all objects')
        subrow = col.row(align=True)
        subrow.alignment = 'EXPAND'
        subrow.label(text='globally, whether they are selected or not.')

        layout.row()

        scene = context.scene
        global min_distance, decimate_ratio
        layout.prop(scene, 'min_distance', 'Minimum distance', 'Minimum distance between elements to merge')

        layout.row()
        layout.operator('grd_panel.remove_doubles_global')
        row = layout.row()
        row.label(text='Decimate:', icon='MOD_DECIM')
        layout.prop(scene, 'decimate_ratio', 'Ratio of triangles to reduce to (collapse only)')

        row = layout.row(align=True)
        row.alignment = 'EXPAND'
        #row.alignment = 'LEFT'
        row.prop(scene, 'decimate_triangulate', 'Triangulate')

        #Symmetry row
        row = layout.row(align=True)
        row.alignment = 'EXPAND'
        split = row.split(percentage=0.5)
        col = split.column(align=True)
        col.alignment = 'LEFT'
        col.prop(scene, 'decimate_symmetry', 'Symmetry')
        col = split.column(align=True)
        col.alignment = 'LEFT'

        if bpy.types.Scene.decimate_symmetry_axis:
            label = str(context.scene.decimate_symmetry_axis)
        else:
            label = "Symmetry Axis"

        #col.operator_menu_enum("decimate_symmetry_axis", context.scene.symmetry_axis_items, text=label)
        col.prop(scene, 'decimate_symmetry_axis', 'Axis')

        layout.row()
        layout.operator('grd_panel.decimate_globally')

        layout.row()
        layout.operator('grd_panel.undecimate_globally')

        global _DEBUG
        if _DEBUG:
            layout.row()
            layout.operator('grd_panel.my_debug')


class OBJECT_OT_UnDecimateGloballyButton(bpy.types.Operator):
    """UnDecimate all meshes globally, aborting on error and reporting it in the console."""
    bl_idname = 'grd_panel.undecimate_globally'
    bl_label = 'Undecimate Meshes'

    def execute(self, context):
        ncount = 0
        ntotal = 0
        try:
            objectList = bpy.data.objects
            for obj in objectList:
                if (obj.type == "MESH"):
                    self.report({'INFO'}, 'Removing decimate modifier %s' % (str(obj),))
                    ncount += removeAllDecimateModifiers(obj)

                    ntotal += 1

            self.report({'INFO'},
                        'Undecimated %d of %d meshes' % (ncount, ntotal))
        except:
            self.report({'ERROR'}, '%s' % (traceback.print_exc(),))
            self.report({'ERROR'},
                        'Abort after %d meshes -- see Info window for details. (Are you in Edit mode?)' % (
                        ncount, ))

        return {'FINISHED'}



class OBJECT_OT_DecimateGloballyButton(bpy.types.Operator):
    """Decimate all meshes globally, aborting on error and reporting it in the console."""
    bl_idname = 'grd_panel.decimate_globally'
    bl_label = 'Decimate Meshes'

    def execute(self, context):
        ncount = 0
        try:
            scene = context.scene
            self.report({'INFO'}, 'Got scene...')
            ratio = scene['decimate_ratio']
            self.report({'INFO'}, 'ratio...')
            triangulate = scene['decimate_triangulate']
            self.report({'INFO'}, 'triangulate...')
            # symmetry = scene['decimate_symmetry']
            # self.report({'INFO'}, 'symmetry...')
            # global symmetry_axis_items
            # symmetry_axis = symmetry_axis_items[scene['decimate_symmetry_axis']]
            # self.report({'INFO'}, 'symmetry_axis = %s...' % (symmetry_axis, ))
            # self.report({'INFO'}, 'Got scene info...')

            #mesh_count = len(bpy.data.meshes)

            objectList = bpy.data.objects
            for obj in objectList:
                self.report({'INFO'}, 'Checking %s' % (str(obj),))
                if obj.type == "MESH":
                    self.report({'INFO'}, 'Decimating %s' % (str(obj),))
                    removeAllDecimateModifiers(obj)
                    self.report({'INFO'}, '  Removed doubles')
                    #bpy.ops.object.modifier_add(type='DECIMATE')
                    modifier = obj.modifiers.new("Decimate", type='DECIMATE')
                    self.report({'INFO'}, '  got modifier')
                    modifier.decimate_type = 'COLLAPSE'
                    self.report({'INFO'}, '  set type')
                    modifier.ratio = ratio
                    self.report({'INFO'}, '  set ratio')
                    modifier.use_collapse_triangulate = triangulate
                    self.report({'INFO'}, '  set use_collapse_triangulate')
                    #modifier.use_symmetry = symmetry
                    #self.report({'INFO'}, '  set symmetry')
                    #modifier.symmetry_axis = symmetry_axis
                    #self.report({'INFO'}, '  set symmetry_axis')

                    ncount += 1
                    self.report({'INFO'}, '  Finished mesh!')

            context.scene.update()
            self.report({'INFO'},
                        'Finished decimating %d meshes)' % (ncount, ))
        except:
            self.report({'ERROR'}, '%s' % (traceback.print_exc(),))
            self.report({'ERROR'},
                        'Abort after %d meshes -- see Info window for details.' % (
                        ncount, ))

        return {'FINISHED'}


class OBJECT_OT_GlobalRemoveDoublesButton(bpy.types.Operator):
    bl_idname = 'grd_panel.remove_doubles_global'
    bl_label = 'Remove Doubles'

    def execute(self, context):
        ncount = 0
        try:
            scene = context.scene

            bm = bmesh.new()
            min_distance = scene['min_distance']
            mesh_count = len(bpy.data.meshes)
            total_verts = 0
            total_verts_removed = 0

            for m in bpy.data.meshes:
                self.report({'INFO'}, 'Processing %s' % (str(m), ) )
                bm.from_mesh(m)
                len1 = len(bm.verts)
                total_verts += len1
                self.report({'INFO'}, 'Processing %s: %d verts' % (str(m), len1 ))
                bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=min_distance)
                len2 = len(bm.verts)
                num_removed = len1-len2
                total_verts_removed += num_removed
                self.report({'INFO'}, 'Processed %s: removed %d of %d verts' % (str(m), (num_removed), len1))
                bm.to_mesh(m)
                m.update()
                bm.clear()
                ncount += 1

            bm.free()
            self.report({'INFO'}, 'Finished %d meshes: Removed %d of %d verts)' % (mesh_count, total_verts_removed, total_verts))
        except:
            self.report({'ERROR'}, '%s' % (traceback.print_exc(), ))
            self.report({'ERROR'}, 'Abort after %d of %d meshes -- see Info window for details. (Are you in Edit mode?): Removed %d of %d verts)' % (ncount, mesh_count, total_verts_removed, total_verts))

        return{'FINISHED'}



class OBJECT_OT_GlobalDebug(bpy.types.Operator):
    bl_idname = 'grd_panel.my_debug'
    bl_label = 'Debug'

    def reportInfo(self, str):
        self.report({'INFO'}, str)

    def execute(self, context):
        self.reportInfo('bpy.types.Scene.symmetry_axis_items:')

        for item in bpy.types.Scene.symmetry_axis_items:
           #self.report({'INFO'}, '%s:' % (str(item), ))
           self.reportInfo('%s: %s (%s) ' % (str(item[0]), str(item[1]), str(item[2])))

        return{'FINISHED'}


def register():
    bpy.utils.register_module(__name__)

def unregister():
    bpy.utils.unregister_module(__name__)
 

if __name__ == "__main__":
    register()
