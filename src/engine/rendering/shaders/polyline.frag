#version 330 core

in vec2 v_texcoord;
out vec4 fragColor;

uniform vec2 u_p1;        // Segment start NDC
uniform vec2 u_p2;        // Segment end NDC
uniform float u_aspect;
uniform vec3 u_color;
uniform float u_tension;  // 0.0 (slack) to 1.0 (max tension)
uniform float u_thickness;

void main() {
    vec2 st = (v_texcoord - 0.5) * 2.0;
    st.x *= u_aspect;

    vec2 start_st = u_p1;
    start_st.x *= u_aspect;
    
    vec2 end_st = u_p2;
    end_st.x *= u_aspect;

    vec2 pa = st - start_st;
    vec2 ba = end_st - start_st;
    
    float h = clamp(dot(pa, ba) / max(1e-5, dot(ba, ba)), 0.0, 1.0);
    float d = length(pa - ba * h);

    float line_width = u_thickness * 0.02;
    float core_width = line_width * 0.35;

    float outer_glow = smoothstep(line_width, 0.0, d);
    float inner_core = smoothstep(core_width, 0.0, d);

    // Color modulates towards red under high tension
    vec3 tension_color = mix(u_color, vec3(1.0, 0.25, 0.25), clamp(u_tension, 0.0, 1.0));
    vec3 final_color = mix(tension_color, vec3(1.0, 1.0, 1.0), inner_core * 0.7);
    
    float alpha = outer_glow * 0.85 + inner_core * 0.15;
    fragColor = vec4(final_color, alpha);
}
