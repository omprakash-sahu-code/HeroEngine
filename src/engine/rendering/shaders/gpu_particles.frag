#version 330 core
in vec2 v_texcoord;
in vec4 v_color;

out vec4 frag_color;

void main() {
    // Distance from center of billboard quad
    float dist = distance(v_texcoord, vec2(0.5));
    if (dist > 0.5) {
        discard;
    }
    
    // Smooth radial falloff (glow intensity)
    float intensity = 1.0 - (dist / 0.5);
    intensity = pow(intensity, 2.2); // Quadratic falloff
    
    frag_color = vec4(v_color.rgb, v_color.a * intensity);
}
