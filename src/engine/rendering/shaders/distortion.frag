#version 330 core

in vec2 v_texcoord;
out vec4 fragColor;

uniform vec2 u_center;
uniform float u_radius;
uniform float u_aspect;
uniform vec3 u_color;
uniform float u_time;
uniform float u_strength;

void main() {
    vec2 st = (v_texcoord - 0.5) * 2.0;
    st.x *= u_aspect;

    vec2 center_st = u_center;
    center_st.x *= u_aspect;

    float dist = length(st - center_st);
    float norm_dist = dist / u_radius;

    // Telekinetic force field swirl deformation
    float angle = atan(st.y - center_st.y, st.x - center_st.x);
    float swirl = sin(angle * 6.0 + u_time * 8.0) * 0.1 * u_strength;

    float ring = abs(norm_dist - (0.8 + swirl)) * 10.0;
    float rim_glow = exp(-ring * 2.5) * u_strength;

    // Inner core warp energy density
    float core_glow = smoothstep(1.0, 0.0, norm_dist) * u_strength * 0.6;

    vec3 final_color = mix(u_color, vec3(1.0, 0.2, 0.3), rim_glow);
    float alpha = clamp(rim_glow + core_glow, 0.0, 1.0);

    fragColor = vec4(final_color, alpha);
}
