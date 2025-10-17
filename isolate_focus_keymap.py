import bpy
from bpy.props import StringProperty, EnumProperty
from bpy_extras.io_utils import ImportHelper

# --- 1. Bl_Info: Add-on Registration Details (Updated for Blender 4.4.0) ---
bl_info = {
    "name": "Isolate and Focus Tool",
    "author": "K-Tech",
    "version": (1, 0, 0), 
    "blender": (4, 1, 0), 
    "location": "3D Viewport, Shortcut: Ctrl + Alt + F",
    "description": "Toggles 'Isolate and Focus' mode for the active object with custom shortcut.",
    "category": "3D View",
}

# --- Shared Variables for Keymap Registration ---
addon_keymaps = []

# --- 2. Scene Property to Track Hidden Objects (Same as before) ---
bpy.types.Scene.isolated_objects_data = bpy.props.StringProperty(
    name="Isolated Objects Data",
    default="",
)

# --- 3. The Core Operator Class (Same as before, with a slight adjustment for context) ---
class VIEW3D_OT_isolate_focus(bpy.types.Operator):
    """Isolate the active object and frame it in the viewport."""
    bl_idname = "view3d.isolate_focus_toggle"
    bl_label = "Isolate and Focus"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        """Enable the operator only if an object is selected."""
        # Ensure we have a valid 3D View context for keymap use
        return context.active_object is not None and context.area.type == 'VIEW_3D'

    def execute(self, context):
        scene = context.scene
        active_obj = context.active_object
        
        # Check if the scene property contains data, indicating the mode is active
        is_isolated = bool(scene.isolated_objects_data)
        
        if not is_isolated:
            # --- ISOLATE MODE (First Click) ---
            
            # 1. Store and Hide
            hidden_names = []
            
            for obj in context.view_layer.objects:
                # We hide all objects except the active one
                if obj.hide_get() == False and obj != active_obj:
                    obj.hide_set(True)
                    hidden_names.append(obj.name)
            
            # 2. Save State
            scene.isolated_objects_data = ",".join(hidden_names)
            
            # 3. Focus
            # We call view_selected without parameters for default frame behavior
            bpy.ops.view3d.view_selected('INVOKE_DEFAULT') 

            self.report({'INFO'}, f"Isolated {active_obj.name} and Framed View.")
            
        else:
            # --- RESTORE MODE (Second Click) ---
            
            # 1. Retrieve Stored Names
            hidden_names = scene.isolated_objects_data.split(',')
            
            # 2. Restore Visibility
            for name in hidden_names:
                obj = scene.objects.get(name)
                # Check obj to prevent crash if object was deleted while isolated
                if obj:
                    obj.hide_set(False)

            # 3. Clear State and Reset View
            scene.isolated_objects_data = ""
            
            

            self.report({'INFO'}, "Scene Restored.")

        return {'FINISHED'}


# --- 4. Addon Preferences for Custom Shortcut ---
class IsolateFocusPreferences(bpy.types.AddonPreferences):
    bl_idname = __name__

    # Property to select the main key (e.g., 'F', 'I', etc.)
    shortcut_key: EnumProperty(
        name="Main Key",
        items=[(item, item, "") for item in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'],
        default='F',
    )
    
    # Property for Ctrl modifier
    use_ctrl: bpy.props.BoolProperty(
        name="Use Ctrl",
        default=True,
    )
    
    # Property for Alt modifier
    use_alt: bpy.props.BoolProperty(
        name="Use Alt",
        default=True,
    )
    
    # Property for Shift modifier
    use_shift: bpy.props.BoolProperty(
        name="Use Shift",
        default=False,
    )

    def draw(self, context):
        layout = self.layout
        layout.label(text="Customize Isolate and Focus Shortcut:")
        
        # Row for the Key
        row = layout.row()
        row.prop(self, "shortcut_key")
        
        # Row for Modifiers
        row = layout.row(align=True)
        row.prop(self, "use_ctrl")
        row.prop(self, "use_alt")
        row.prop(self, "use_shift")
        
        layout.label(text="Changes require re-enabling the addon.")

# --- 5. Keymap Registration Logic ---

def register_keymaps():
    # Clear any previous keymaps from this addon
    unregister_keymaps() 

    # Get the addon preferences
    prefs = bpy.context.preferences.addons[__name__].preferences
    
    # Define the keymap parameters
    wm = bpy.context.window_manager
    km = wm.keyconfigs.addon.keymaps.new(name='3D View', space_type='VIEW_3D')
    
    # Add a new keymap item (kmi)
    kmi = km.keymap_items.new(
        VIEW3D_OT_isolate_focus.bl_idname, 
        type=prefs.shortcut_key, 
        value='PRESS', 
        ctrl=prefs.use_ctrl, 
        alt=prefs.use_alt, 
        shift=prefs.use_shift
    )
    
    # Store the created keymap for clean unregistration
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
    
    # Register the custom property
    if not hasattr(bpy.types.Scene, 'isolated_objects_data'):
        bpy.types.Scene.isolated_objects_data = StringProperty(default="")
    
    # Register the keymap
    register_keymaps()
    print("Isolate and Focus Tool Registered with Keymap!")

def unregister():
    """Called when the add-on is disabled."""
    
    # Unregister the keymap FIRST
    unregister_keymaps()
    
    # Clean up the custom property when unregistering
    if hasattr(bpy.types.Scene, 'isolated_objects_data'):
        del bpy.types.Scene.isolated_objects_data
        
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    print("Isolate and Focus Tool Unregistered!")

if __name__ == "__main__":
    register()