import bpy

### All credit for the Apex Shader node groups goes to Ed O'Connell: @llennoco22
### https://twitter.com/llennoco22/status/1152387226241851392
### All I did was allow you to mix between 'em.

### THIS IS A SCRIPT THAT, WHEN RUN, ATTEMPTS TO CONVERT
### ALL MATERIALS IN THE PROJECT TO NODE MATERIALS USING
### A SHADER GROUP FOR APEX TEXTURES.
### ALL MATERIALS BECOME APEX TEXTURES -> SHADER GROUP -> OUTPUT.
### By default, the "emissions" texture isn't connected, but sometimes
### will need to be--especially for glowing materials. Not sure? Connect
### emissions and if it doesn't change the whole material white, it's good.
### THE SHADER GROUP ALLOWS FOR EASY TOGGLING BETWEEN EEVEE AND CYCLES.
### It's set to Eevee by default. You can swap by setting "Cycles Influence"
### to 1 or 0 in the material node.
### You might also want to change the Normals influence. It's also available
### in the material node and changes both Eevee and Cycles' settings.

### YOU'LL NEED:
### > An Apex Model (probably extracted by Legion)
### > Textures extracted by GameImageUtils
### > My Apex Mix Shader.blend file
### > ctrl+f "MODELS_PATH" in this doc and change to suit your operating system
### > ctrl+f "MODEL_NAME" in this doc and change to suit the model you're working with

### TO USE
### > Open Blender and the Apex model
### > Append my Apex Mix Shader.blend file, go to NodeTree, select Apex Mix Shader
### > Click "new" or open this file in the Scripting tab of Blender
### > Click the play button
### > Done!

### ERROR MANAGEMENT
### If you're told the script failed, go to Window -> Toggle System Console, see what
### the bottom message says
### If it said it couldn't find something, it's likely you forgot to append the shader
### If it couldn't find the right directory, check your file variables
### If it didn't add any textures, check your file variables
### If some of the textures aren't being lit properly, edit the nodes' Normal strengths
### If something is pure white, it's likely you connected a bad Emission.
### For other material issues, compare the textures to those in _images in your model
### folder and replace as necessary, and try swapping materials around: sometimes the
### exported files get named improperly. Compare, e.g. your AO texture to a working AO:
### maybe your AO is actually a cavity map, or an albedo, or...

### CHANGE THESE VARIABLES
MODEL_NAME = "loba_v20_chaostheory_w"
MODELS_PATH = "C:\\Users\\jaspi\\Downloads\\LegionReleasev2.24\\exported_files\\models\\" # (use double slashes!)
### CHANGE THESE VARIABLES

MODEL_PATH = MODELS_PATH + MODEL_NAME

DEBUG_MODE = False # Need print statements for debugging? Turn this on.

def setup_material(material):
    '''
    Function: setup_material
    Summary: Performs initial setup on a material before adding nodes to it to suit the Apex Mix Shader. Only functional on materials with an existing node graph.
    Attributes: 
        @param (material): object The material we're altering.
    '''
    mat_string = material.name
    if mat_string == "wraith_eye_shadow" or mat_string == "wraith_eye_cornea":
        material.blend_method = "BLEND" # These are going to be partially transparent.
    if DEBUG_MODE: print("working on " + mat_string)
    node_tree = material.node_tree
    
    if not node_tree or not node_tree.nodes:
        return

    node_tree.nodes.clear()
    if mat_string == "wraith_eye_shadow":
        wraith_eyeshadow(node_tree, MODEL_PATH + "\\" + mat_string + "\\") # We handle this material specially.
        return

    create_material_nodes(node_tree, mat_string)

def create_material_nodes(node_tree, mat_string):
    '''
    Function: create_material_nodes
    Summary: Sets up a full node graph for a given material.
    Attributes: 
        @param (node_tree): object The shader graph for this material.
        @param (mat_string): string The name of this material, e.g. "crypto_head_...".
    '''
    mix_shader = node_tree.nodes.new(type="ShaderNodeGroup")
    mix_shader.location = (-200, 0)
    mix_shader.node_tree = bpy.data.node_groups["Apex Mix Shader"]
    mix_shader.node_tree.inputs[0].default_value = 0
    if DEBUG_MODE: print(mat_string)
    if mat_string == "wraith_eye_cornea":
        mix_shader.inputs[2].default_value = 1 # sets the Transparency to 1

    texture_types = ( "albedo", "specular", "gloss", "normal", "emissive", "ao" )
    links = ( 
        [["Color", "Albedo"]], 
        [["Color", "Specular"]],
        [["Color", "Glossiness"]], 
        [["Color", "Normalmap"]], 
        None, 
        [["Color", "Ambient Occlusion"]] 
    )
    node_locs = ( (-500, 200), (-500, 100), (-500, 0), (-500, -100), (-500, -200), (-500, -300) ) 
    material_textures_path = MODEL_PATH + "\\" + mat_string + "\\" + mat_string
    if DEBUG_MODE: print("Our textures are under " + material_textures_path)
    for i in range(len(texture_types)):
        tex_node = add_texture(
            texture_types[i], 
            links[i], 
            node_locs[i], 
            mix_shader, 
            node_tree,
            material_textures_path
        )

    node_out = node_tree.nodes.new(type="ShaderNodeOutputMaterial")
    node_tree.links.new(node_out.inputs["Surface"], mix_shader.outputs["Shader"])

def add_texture(texture_type, links, node_loc, node_out, node_tree, textures_path):
    '''
    Function: add_texture
    Summary: Imports a texture image from a file path constructed from its parameters, linking it to the given BSDF node in the given way.
    Attributes: 
        @param (texture_type): string Type of texture, e.g. "albedo" 
        @param (links): array(array(string)) Links to be made between nodes, e.g. between "Color" and "Albedo"
        @param (node_loc): array(int) The location for this texture to be placed in the shader graph
        @param (node_out): Object The output node we'll connect this texture to
        @param (node_tree): Object The shader graph we're working within
        @param (textures_path): string The path to all textures for this material
    Returns: object If successful, returns a texture image input node. If unsuccessful, returns None.
    '''
    if DEBUG_MODE: print("adding texture " + texture_type)
    tex = node_tree.nodes.new("ShaderNodeTexImage")
    tex.location = node_loc
    path = textures_path + "_" + texture_type + ".png"
    if DEBUG_MODE: print(path)
    try:
        image = bpy.data.images.load(path)
        tex.image = image
        if links:
            for link in links:
                node_tree.links.new(node_out.inputs[link[1]], tex.outputs[link[0]])
        tex.hide = True
        return tex
    except:
        node_tree.nodes.remove(tex)
        return None

def wraith_eyeshadow(node_tree, material_folder_path):
    '''
    Function: wraith_eyeshadow
    Summary: Performs a special setup for the wraith_eye_shadow material, connecting just its albedo to a normal BSDF.
    Attributes: 
        @param (node_tree): object The shader graph we're working within.
        @param (material_folder_path): string The folder containing the material we're working with.
    '''
    bsdf = node_tree.nodes.new(type="ShaderNodeBsdfPrincipled")
    bsdf.location = (-200, 0)
    textures_path = material_folder_path + "wraith_eye_shadow"

    add_texture(
        "albedo", 
        [["Color", "Base Color"], ["Alpha", "Alpha"]], 
        (-500, -200), 
        bsdf,
        node_tree,
        textures_path
    )

    node_out = node_tree.nodes.new(type="ShaderNodeOutputMaterial")
    node_tree.links.new(node_out.inputs["Surface"], bsdf.outputs["BSDF"])

print("Fixing materials.")

for mat in bpy.data.materials:
    setup_material(mat)

print("Done fixing materials.")
