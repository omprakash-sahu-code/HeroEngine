#version 330 core

in vec2 v_texcoord;
out vec4 fragColor;

uniform vec2 u_center;
uniform float u_radius;
uniform float u_aspect;
uniform vec3 u_color;
uniform float u_charge;   // 0.0 to 1.0
uniform float u_time;
uniform int u_mode;       // 0 = RING, 1 = BEAM, 2 = FLASH
uniform vec2 u_beam_end;  // End position of laser beam

void main() {
    vec2 st = (v_texcoord - 0.5) * 2.0;
    st.x *= u_aspect;
    
    vec2 center_st = u_center;
    center_st.x *= u_aspect;

    if (u_mode == 0) {
        // REPULSOR RING (Concentric pulsing energy rings)
        float d = length(st - center_st);
        
        // Ring 1 (outer pulsing ring)
        float r1 = u_radius * (0.8 + 0.2 * sin(u_time * 8.0));
        float ring1 = smoothstep(0.015, 0.0, abs(d - r1));
        
        // Ring 2 (inner charging ring scaled by charge level)
        float r2 = u_radius * 0.5 * u_charge;
        float ring2 = smoothstep(0.02, 0.0, abs(d - r2));
        
        // Inner glowing core
        float core = smoothstep(r2, 0.0, d) * u_charge;
        
        float alpha = (ring1 * 0.7 + ring2 * 0.9 + core * 0.6) * u_charge;
        fragColor = vec4(u_color * (1.2 + ring2), alpha);
        
    } else if (u_mode == 1) {
        // REPULSOR BEAM (High-energy laser blast along line segment)
        vec2 start_st = center_st;
        vec2 end_st = u_beam_end;
        end_st.x *= u_aspect;
        
        vec2 pa = st - start_st;
        vec2 ba = end_st - start_st;
        float h = clamp(dot(pa, ba) / dot(ba, ba), 0.0, 1.0);
        float d = length(pa - ba * h);
        
        float beam_width = u_radius * 0.25;
        float core_width = beam_width * 0.4;
        
        float outer_glow = smoothstep(beam_width, 0.0, d);
        float inner_core = smoothstep(core_width, 0.0, d);
        
        vec3 final_color = mix(u_color, vec3(1.0, 1.0, 1.0), inner_core);
        float alpha = outer_glow * 0.9 + inner_core * 0.1;
        fragColor = vec4(final_color, alpha);
        
    } else if (u_mode == 2) {
        // REPULSOR FLASH (Muzzle explosion at palm origin)
        float d = length(st - center_st);
        float flash = smoothstep(u_radius, 0.0, d);
        float rays = sin(atan(st.y - center_st.y, st.x - center_st.x) * 12.0 + u_time * 20.0) * 0.5 + 0.5;
        
        float alpha = flash * (0.8 + 0.2 * rays);
        vec3 col = mix(u_color, vec3(1.0, 1.0, 1.0), flash * 0.6);
        fragColor = vec4(col, alpha);
    } else {
        fragColor = vec4(0.0);
    }
}
