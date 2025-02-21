import bpy
import bmesh
from mathutils import Vector
from bpy.types import WorkSpaceTool
from bl_ui.properties_paint_common import UnifiedPaintPanel
from bpy_extras import view3d_utils

class CustomVertexPaintTool(WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'PAINT_VERTEX'

    bl_idname = "vertex_face_paint.tool"
    bl_label = "Vertex Face Paint"
    bl_description = "Paint vertex colors by mesh faces"
    bl_icon = "brush.sculpt.paint"
    bl_widget = None
    bl_keymap = (
        ("vertex_face_paint.operator", {"type": 'LEFTMOUSE', "value": 'PRESS'}, None),
    )

    @classmethod
    def draw_settings(cls, context, layout, tool):
        props = tool.operator_properties("vertex_face_paint.operator")
        brush = context.tool_settings.vertex_paint.brush
        
        # Add Unified Paint Panel color settings
        col = layout.column()
        UnifiedPaintPanel.prop_unified_color(col, context, brush, "color", text="")
        col.prop(brush, "use_gradient", text="Gradient")
        
        # Add brush settings
        col = layout.column(align=True)
        col.prop(brush, "strength", slider=True)
        col.prop(props, "brush_alpha", slider=True)
        col.prop(props, "apply_alpha")

class CustomVertexPaintOperator(bpy.types.Operator):
    bl_idname = "vertex_face_paint.operator"
    bl_label = "Vertex Face Paint"
    bl_options = {'REGISTER', 'UNDO'}

    brush_alpha: bpy.props.FloatProperty(
        name="Alpha",
        default=1.0,
        min=0.0,
        max=1.0
    )
    apply_alpha: bpy.props.BoolProperty(
        name="Apply Alpha",
        default=False,
    )

    _did_paint = False

    def modal(self, context, event):
        if event.type == 'MOUSEMOVE':
            self._did_paint = True
            self.paint(context, event)
        elif event.type == 'LEFTMOUSE':
            if event.value == 'RELEASE':
                if self._did_paint:
                    self._did_paint = False
                else: 
                    self.paint(context, event)
                return {'FINISHED'}
        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            self._did_paint = False
            return {'CANCELLED'}
        
        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        if context.object.data.vertex_colors.active is None:
            self.report({'WARNING'}, "No vertex color attribute layer")
            return {'CANCELLED'}

        if context.object and context.object.type == 'MESH':
            context.window.cursor_set('PAINT_BRUSH')
            context.window_manager.modal_handler_add(self)
            return {'RUNNING_MODAL'}
        else:
            self.report({'WARNING'}, "No active mesh object")
            return {'CANCELLED'}

    def paint(self, context, event):
        obj = context.object
        vertex_color_layer = obj.data.vertex_colors.active
        brush = context.tool_settings.vertex_paint.brush
        brush_color = brush.color

        region = context.region
        rv3d = context.region_data
        coord = event.mouse_region_x, event.mouse_region_y
        
        view_vector = view3d_utils.region_2d_to_vector_3d(region, rv3d, coord)
        ray_origin = view3d_utils.region_2d_to_origin_3d(region, rv3d, coord)
        
        hit, location, normal, face_index, object, matrix = context.scene.ray_cast(
            context.view_layer.depsgraph, ray_origin, view_vector)
        
        if hit:
            face = obj.data.polygons[face_index]
            for loop_index in face.loop_indices:
                alpha = self.brush_alpha * brush.strength
                if not self.apply_alpha:
                    alpha = Vector(vertex_color_layer.data[loop_index].color).w
                new_color = Vector((brush_color.r, brush_color.g, brush_color.b, alpha))
                vertex_color_layer.data[loop_index].color = new_color
        
        obj.data.update()

def register():
    bpy.utils.register_class(CustomVertexPaintOperator)
    bpy.utils.register_tool(CustomVertexPaintTool, separator=True, group=True)

def unregister():
    bpy.utils.unregister_tool(CustomVertexPaintTool)
    bpy.utils.unregister_class(CustomVertexPaintOperator)

if __name__ == "__main__":
    register()