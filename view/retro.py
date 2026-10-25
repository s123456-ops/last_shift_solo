"""PS1 horror style: low resolution, reduced colours and dithering.

A single shader (a small program run by the graphics card) retouches the
camera image. Rules, map and models do not change, and the interface
(HUD, plan, menus) stays sharp, because it has its own camera.
"""

from ursina import Shader, camera

VIRTUAL_HEIGHT = 240  # lines of pixels on screen, like the PlayStation
COLOR_LEVELS = 32  # shades per primary colour (15 bits, like the PS1)
DITHER_STRENGTH = 1.0  # dithering: 0 = flat areas and visible banding, 1 = period grain

# The GLSL code stays ASCII: some graphics drivers reject accented characters.
_VERTEX = """
#version 150
uniform mat4 p3d_ModelViewProjectionMatrix;
in vec4 p3d_Vertex;
in vec2 p3d_MultiTexCoord0;
out vec2 uv;

void main() {
    gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;
    uv = p3d_MultiTexCoord0;
}
"""

_FRAGMENT = """
#version 150
uniform sampler2D tex;
in vec2 uv;
out vec4 color;

const float VIRTUAL_HEIGHT = {virtual_height:.1f};
const float COLOR_LEVELS = {color_levels:.1f};
const float DITHER_STRENGTH = {dither_strength:.2f};
// Bayer 4x4 matrix: the order in which pixels light up when dithering.
const mat4 BAYER = mat4(
     0.0,  8.0,  2.0, 10.0,
    12.0,  4.0, 14.0,  6.0,
     3.0, 11.0,  1.0,  9.0,
    15.0,  7.0, 13.0,  5.0
);

void main() {{
    // 1. Low resolution: every real pixel of a big pixel reads the same point.
    vec2 screen = vec2(textureSize(tex, 0));
    vec2 virtual_size = vec2(VIRTUAL_HEIGHT * screen.x / screen.y, VIRTUAL_HEIGHT);
    vec2 big_pixel = floor(uv * virtual_size);
    vec3 rgb = texture(tex, (big_pixel + 0.5) / virtual_size).rgb;

    // 2. Dithering: a small offset that depends on the big pixel position.
    int x = int(mod(big_pixel.x, 4.0));
    int y = int(mod(big_pixel.y, 4.0));
    float threshold = BAYER[x][y] / 16.0 - 0.5;
    rgb += threshold * DITHER_STRENGTH / COLOR_LEVELS;

    // 3. Fewer colors: each channel is rounded to one of the levels.
    rgb = floor(rgb * COLOR_LEVELS + 0.5) / COLOR_LEVELS;
    color = vec4(clamp(rgb, 0.0, 1.0), 1.0);
}}
"""


def _build_shader() -> Shader:
    fragment = _FRAGMENT.format(
        virtual_height=VIRTUAL_HEIGHT,
        color_levels=COLOR_LEVELS,
        dither_strength=DITHER_STRENGTH,
    )
    return Shader(language=Shader.GLSL, vertex=_VERTEX, fragment=fragment)


_shader: Shader | None = None


def set_retro_style(enabled: bool) -> None:
    """Applies or removes the PS1 style on the game image."""
    global _shader
    if not enabled:
        camera.shader = None
        return
    if _shader is None:
        _shader = _build_shader()  # created only once, the first time it is needed
    camera.shader = _shader
