#version 330 core
in vec2 v_texcoord;
out vec4 frag_color;

uniform sampler2D u_texture;
uniform float u_threshold;

void main() {
    vec4 color = texture(u_texture, v_texcoord);
    // Relative luminance calculation for standard sRGB primaries
    float brightness = dot(color.rgb, vec3(0.2126, 0.7152, 0.0722));
    
    if (brightness > u_threshold) {
        frag_color = color;
    } else {
        frag_color = vec4(0.0, 0.0, 0.0, 1.0);
    }
}
