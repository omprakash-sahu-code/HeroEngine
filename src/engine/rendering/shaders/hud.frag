#version 330 core

in vec2 v_texcoord;
out vec4 fragColor;

uniform vec2 u_center;
uniform float u_radius;
uniform float u_aspect;
uniform vec3 u_color;
uniform float u_time;
uniform float u_locked;   // 0.0 = searching, 1.0 = locked target
uniform float u_rotation;

void main() {
    vec2 st = (v_texcoord - 0.5) * 2.0;
    st.x *= u_aspect;
    
    vec2 center_st = u_center;
    center_st.x *= u_aspect;
    
    vec2 p = st - center_st;
    
    // Rotate coordinates for rotating HUD reticle brackets
    float cos_r = cos(u_rotation);
    float sin_r = sin(u_rotation);
    vec2 rot_p = vec2(
        cos_r * p.x - sin_r * p.y,
        sin_r * p.x + cos_r * p.y
    );
    
    float d = length(p);
    
    // Outer dashed ring
    float outer_ring = smoothstep(0.01, 0.0, abs(d - u_radius));
    float dashes = step(0.5, sin(atan(rot_p.y, rot_p.x) * 8.0));
    outer_ring *= dashes;
    
    # Target crosshair lines
    float crosshair = smoothstep(0.005, 0.0, abs(rot_p.x)) * step(d, u_radius * 1.2) * step(u_radius * 0.4, d) +
                      smoothstep(0.005, 0.0, abs(rot_p.y)) * step(d, u_radius * 1.2) * step(u_radius * 0.4, d);
                      
    // Center lock indicator dot
    float center_dot = smoothstep(0.015 * (1.0 + 0.5 * u_locked), 0.0, d);
    
    // Lock pulsing ring
    float lock_ring = smoothstep(0.012, 0.0, abs(d - u_radius * 0.5)) * u_locked;
    
    vec3 final_color = mix(u_color, vec3(1.0, 0.2, 0.2), u_locked * 0.8);
    float alpha = (outer_ring * 0.8 + crosshair * 0.7 + center_dot * 0.9 + lock_ring * 0.9);
    
    fragColor = vec4(final_color, alpha * 0.85);
}
