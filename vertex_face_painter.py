import bpy
import bmesh
from mathutils import Vector
from bpy.types import WorkSpaceTool
from bpy_extras import view3d_utils
from bl_ui.properties_paint_common import (
    ColorPalettePanel,
    UnifiedPaintPanel
)

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
        vpaint_settings = context.tool_settings.vertex_paint
        vbrush = vpaint_settings.brush
        vpalette = vpaint_settings.palette
        
        # Use split layout for primary and secondary colors
        #row = layout.row()
        split = layout.split(factor=0.5)
        split.prop(vbrush, "color")
        split.prop(vbrush, "secondary_color")
        #UnifiedPaintPanel.prop_unified_color(split, context, vbrush, "color")
        #UnifiedPaintPanel.prop_unified_color(split, context, vbrush, "secondary_color")
        
        # Add blend mode and strength
        layout.prop(vbrush, "blend", text="Blend Mode")
        layout.prop(vbrush, "strength", slider=True)
        
        layout.separator()

        [panel_c_head, panel_c] = layout.panel(idname="vertex_face_paint.colorpalettepanel")
        panel_c_head.label(text="Color Palette")
        # Add color palette if available
        panel_c.template_ID(vpaint_settings, "palette", new="palette.new")
        if vpalette:
            panel_c.template_palette(vpaint_settings, "palette", color=True)

        [panel_a_head, panel_a] = layout.panel(idname="vertex_face_paint.alphachannelpanel")
        panel_a_head.label(text="Alpha Channel")
        panel_a.prop(props, "brush_alpha")
        panel_a.prop(props, "apply_alpha")

class CustomVertexPaintOperator(bpy.types.Operator):
    bl_idname = "vertex_face_paint.operator"
    bl_label = "Vertex Face Paint"
    bl_options = {'REGISTER', 'UNDO'}


    apply_alpha: bpy.props.BoolProperty(
        name="Apply Alpha Value",
        description="Vertices colors will include an alpha value, supplied by the preference and is NOT blended.",
        default=False,
    )
    brush_alpha: bpy.props.FloatProperty(
        name="Alpha Value",
        default=(1.0),
        min=0.0,
        max=1.0
    )

    _did_paint = False

    def modal(self, context, event):
        #TODO Undo support
        #TODO brush speed
        if event.type == 'MOUSEMOVE':
            self._did_paint = True
            self.paint(context, event)
        elif event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
            if self._did_paint:
                self._did_paint = False
            else:
                self.paint(context, event)
                self._did_paint = True
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
        
        hit, _, _, face_index, _, _ = context.scene.ray_cast(
            context.view_layer.depsgraph, ray_origin, view_vector)
        
        if hit:
            face = obj.data.polygons[face_index]
            for loop_index in face.loop_indices:
                current_color = vertex_color_layer.data[loop_index].color
                if self.apply_alpha:
                     [_,_,_, alpha] = current_color
                     current_color[3] = self.brush_alpha
                new_color = self.blend_colors(current_color, brush_color, brush.strength, brush.blend)
                vertex_color_layer.data[loop_index].color = new_color
        

        
        obj.data.update()

    @staticmethod
    def blend_colors(current_color, brush_color, strength, blend_mode):
        def clamp01(x):
            return min(max(x, 0.0), 1.0)
        
        cr, cg, cb, ca = current_color
        br, bg, bb = brush_color.r, brush_color.g, brush_color.b
        
        #TODO Blend modes
        # Overlay blend mode for RGB
        if blend_mode == 'OVERLAY':
            rgb = []
            for base, overlay in zip((cr, cg, cb), (br, bg, bb)):
                if overlay <= 0.5:
                    result = 2 * base * overlay
                else:
                    result = 1 - 2 * (1 - base) * (1 - overlay)
                blended = base * (1 - strength) + result * strength
                rgb.append(clamp01(blended))
            r, g, b = rgb
        else:  # Fallback to Mix if overlay isn't selected
            r = cr * (1 - strength) + br * strength
            g = cg * (1 - strength) + bg * strength
            b = cb * (1 - strength) + bb * strength
            r, g, b = clamp01(r), clamp01(g), clamp01(b)
        
        return Vector((r, g, b, ca))

def register():
    bpy.utils.register_class(CustomVertexPaintOperator)
    bpy.utils.register_tool(CustomVertexPaintTool, separator=True, group=True)

def unregister():
    bpy.utils.unregister_tool(CustomVertexPaintTool)
    bpy.utils.unregister_class(CustomVertexPaintOperator)

if __name__ == "__main__":
    register()