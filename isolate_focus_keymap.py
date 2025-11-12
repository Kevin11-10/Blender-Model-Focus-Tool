import bpy
from bpy.props import StringProperty, EnumProperty, FloatVectorProperty, FloatProperty
from bpy_extras.io_utils import ImportHelper

# --- 1. Bl_Info: Add-on Registration Details ---
bl_info = {
    "name": "Isolate and Focus Tool (View Restore Final Fix)",
    "author": "K3D Studio",
    "version": (1, 1, 3), 
    "blender": (4, 1, 0), 
    "location": "3D Viewport, Shortcut: Ctrl + Alt + F",
    "description": "Toggles 'Isolate and Focus' mode for the active object, reliably restoring the previous viewport view.",
    "category": "3D View",
}

# --- Shared Variables for Keymap Registration ---
addon_keymaps = []


# --- Helper Function to Get the Active 3D View Data ---
def get_view3d_region_data(context):
    """Finds and returns the active 3D View region data."""
    if context.area and context.area.type == 'VIEW_3D':
        for region in context.area.regions:
            if region.type == 'WINDOW':
                # This region contains the view data we need
                return region.data
    return None


# --- 3. The Core Operator Class (Using Location/Rotation/Distance) ---
class VIEW3D_OT_isolate_focus(bpy.types.Operator):
    """Isolate the active object and frame it in the viewport."""
    bl_idname = "view3d.isolate_focus_toggle"
    bl_label = "Isolate and Focus (Toggle)"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        """Enable the operator only if an object is selected and we are in VIEW_3D."""
        return context.active_object is not None and context.area and context.area.type == 'VIEW_3D'

    def execute(self, context):
        scene = context.scene
        active_obj = context.active_object
        rv3d = get_view3d_region_data(context)
        
        if not rv3d:
            self.report({'ERROR'}, "Could not find 3D Viewport data.")
            return {'CANCELLED'}
        
        # Check if the scene property contains data, indicating the mode is active
        is_isolated = bool(scene.isolated_objects_data)
        
        if not is_isolated:
            # --- ISOLATE MODE (First Click) ---
            
            # 1. SAVE VIEW STATE: Save location, rotation, AND DISTANCE
            scene.saved_view_location = rv3d.view_location
            scene.saved_view_rotation = rv3d.view_rotation
            scene.saved_view_distance = rv3d.view_distance
            
            # 2. Store and Hide
            hidden_names = []
            for obj in context.view_layer.objects: 
                if obj.hide_get() == False and obj != active_obj:
                    obj.hide_set(True)
                    hidden_names.append(obj.name)
            
            # 3. Save State
            scene.isolated_objects_data = ",".join(hidden_names)
            
            # 4. Focus (Changes the view)
            bpy.ops.view3d.view_selected('INVOKE_DEFAULT') 

            self.report({'INFO'}, f"Isolated {active_obj.name} and Framed View.")
            
        else:
            # --- RESTORE MODE (Second Click) ---
            
            # 1. Retrieve Stored Names
            hidden_names = scene.isolated_objects_data.split(',')
            
            # 2. Restore Visibility
            for name in hidden_names:
                obj = scene.objects.get(name)
                if obj:
                    obj.hide_set(False)

            # 3. RESTORE VIEW STATE: Restore location, rotation, AND DISTANCE
            rv3d.view_location = scene.saved_view_location
            rv3d.view_rotation = scene.saved_view_rotation
            rv3d.view_distance = scene.saved_view_distance
            
            # 4. Clear State
            scene.isolated_objects_data = ""
            scene.saved_view_location = [0.0] * 3
            scene.saved_view_rotation = [0.0] * 4
            scene.saved_view_distance = 0.0 # Clear distance property
            
            self.report({'INFO'}, "Scene and View Restored.")

        return {'FINISHED'}


# --- 4. Addon Preferences ---
class IsolateFocusPreferences(bpy.types.AddonPreferences):
    bl_idname = __name__

    shortcut_key: EnumProperty(
        name="Main Key",
        items=[(item, item, "") for item in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'],
        default='F',
    )
    
    use_ctrl: bpy.props.BoolProperty(
        name="Use Ctrl",
        default=True,
    )
    
    use_alt: bpy.props.BoolProperty(
        name="Use Alt",
        default=True,
    )
    
    use_shift: bpy.props.BoolProperty(
        name="Use Shift",
        default=False,
    )

    def draw(self, context):
        layout = self.layout
        layout.label(text="Customize Isolate and Focus Shortcut:")
        
        row = layout.row()
        row.prop(self, "shortcut_key")
        
        row = layout.row(align=True)
        row.prop(self, "use_ctrl")
        row.prop(self, "use_alt")
        row.prop(self, "use_shift")
        
        layout.label(text="Changes require re-enabling the addon.")

# --- 5. Keymap Registration Logic ---

def register_keymaps():
    unregister_keymaps() 

    try:
        prefs = bpy.context.preferences.addons[__name__].preferences
    except KeyError:
        return
    
    wm = bpy.context.window_manager
    km = wm.keyconfigs.addon.keymaps.new(name='3D View', space_type='VIEW_3D')
    
    kmi = km.keymap_items.new(
        VIEW3D_OT_isolate_focus.bl_idname, 
        type=prefs.shortcut_key, 
        value='PRESS', 
        ctrl=prefs.use_ctrl, 
        alt=prefs.use_alt, 
        shift=prefs.use_shift
    )
    
    addon_keymaps.append(km)

def unregister_keymaps():
    wm = bpy.context.window_manager
    for km in addon_keymaps:
        wm.keyconfigs.addon.keymaps.remove(km)
    addon_keymaps.clear()

# --- 6. Registration/Unregistration Functions ---

classes = (
    VIEW3D_OT_isolate_focus,
    IsolateFocusPreferences
)

def register():
    """Called when the add-on is enabled."""
    for cls in classes:
        bpy.utils.register_class(cls)
    
    # Register the custom properties (View Restore Fix properties)
    bpy.types.Scene.isolated_objects_data = StringProperty(default="")
    bpy.types.Scene.saved_view_location = FloatVectorProperty(size=3, default=[0.0] * 3)
    bpy.types.Scene.saved_view_rotation = FloatVectorProperty(size=4, default=[0.0] * 4)
    bpy.types.Scene.saved_view_distance = FloatProperty(default=0.0) # <-- NEW PROPERTY REGISTRATION
    
    # Register the keymap
    register_keymaps()
    print("Isolate and Focus Tool Registered with Keymap!")

def unregister():
    """Called when the add-on is disabled."""
    
    # Unregister the keymap FIRST
    unregister_keymaps()
    
    # Clean up the custom properties when unregistering
    if hasattr(bpy.types.Scene, 'isolated_objects_data'):
        del bpy.types.Scene.isolated_objects_data
    if hasattr(bpy.types.Scene, 'saved_view_location'):
        del bpy.types.Scene.saved_view_location
    if hasattr(bpy.types.Scene, 'saved_view_rotation'):
        del bpy.types.Scene.saved_view_rotation
    if hasattr(bpy.types.Scene, 'saved_view_distance'):
        del bpy.types.Scene.saved_view_distance # <-- NEW PROPERTY CLEANUP
        
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    print("Isolate and Focus Tool Unregistered!")

if __name__ == "__main__":
    register()
