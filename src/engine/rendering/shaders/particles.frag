#version 330 core
in vec4 v_color;

out vec4 frag_color;

void main() {
    // Render point sprites as soft glowing circles instead of flat squares
    vec2 coord = gl_PointCoord - vec2(0.5);
    float dist = length(coord);
    
    if (dist > 0.5) {
        discard;
    }
    
    // Soft radial falloff for glow
    float alpha = v_color.a * (1.0 - smoothstep(0.1, 0.5, dist));
    frag_color = vec4(v_color.rgb, alpha);
}
