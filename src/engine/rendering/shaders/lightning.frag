#version 330 core

in vec2 v_texcoord;
out vec4 fragColor;

uniform vec2 u_center;
uniform float u_radius;
uniform float u_aspect;
uniform vec3 u_color;
uniform float u_time;
uniform float u_charge;

float hash(vec2 p) {
    p = fract(p * vec2(123.34, 456.21));
    p += dot(p, p + 45.32);
    return fract(p.x * p.y);
}

float noise(vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    f = f * f * (3.0 - 2.0 * f);
    float a = hash(i);
    float b = hash(i + vec2(1.0, 0.0));
    float c = hash(i + vec2(0.0, 1.0));
    float d = hash(i + vec2(1.0, 1.0));
    return mix(mix(a, b, f.x), mix(c, d, f.x), f.y);
}

void main() {
    vec2 st = (v_texcoord - 0.5) * 2.0;
    st.x *= u_aspect;

    vec2 center_st = u_center;
    center_st.x *= u_aspect;

    float dist = length(st - center_st);
    float norm_dist = dist / u_radius;

    // Procedural electrical jitter noise
    float angle = atan(st.y - center_st.y, st.x - center_st.x);
    float electric_noise = noise(vec2(angle * 4.0, u_time * 15.0)) * 0.15;

    float ring = abs(norm_dist - (0.6 + electric_noise)) * 12.0;
    float core_intensity = exp(-ring * 2.0) * u_charge;
    float outer_glow = smoothstep(1.2, 0.0, norm_dist) * u_charge * 0.5;

    vec3 final_color = mix(u_color, vec3(1.0, 1.0, 1.0), core_intensity);
    float alpha = clamp(core_intensity + outer_glow, 0.0, 1.0);

    fragColor = vec4(final_color, alpha);
}
