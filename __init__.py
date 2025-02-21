# Copyright 2022 by Hextant Studios. https://HextantStudios.com
# This work is licensed under GNU General Public License Version 3.
# License: https://download.blender.org/release/GPL3-license.txt

bl_info = {
    "name": "Vertex Face Paint Tool",
    "author": "zvodd",
    "version": (1, 0),
    "blender": (3, 60, 0),
    "location": "View3D > Vertex Paint Mode",
    "description": "A vertex painting tool that works on mesh faces",
    "category": "Paint",
}
import bpy

# Include *all* modules in this package for proper reloading.
#   * All modules *must* have a register() and unregister() method!
#   * Dependency *must* come *before* modules that use them in the list!
register, unregister = bpy.utils.register_submodule_factory(__package__, (
    'vertex_face_painter',
))