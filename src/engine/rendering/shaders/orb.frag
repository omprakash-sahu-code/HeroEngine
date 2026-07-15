#version 330 core
in vec2 v_texcoord;
in vec2 v_local_pos;

out vec4 frag_color;

uniform float u_time;
uniform vec3 u_color; // Default color theme

// Simplex-like pseudo-noise helper
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
    float dist = length(v_local_pos);
    
    // Soft circular mask
    if (dist > 1.0) {
        discard;
    }
    
    // Animated noise for energy ripple effect
    vec2 uv_noise = vec2(atan(v_local_pos.y, v_local_pos.x) * 2.0, dist * 5.0 - u_time * 8.0);
    float n = noise(uv_noise);
    
    // Core and glow layers
    float glow = exp(-2.8 * dist);
    float core = 1.0 - smoothstep(0.0, 0.35, dist);
    
    // Pulsing alpha
    float pulse = 0.85 + 0.15 * sin(u_time * 12.0);
    
    // Combine layers to form bright glowing plasma
    float intensity = (glow * 0.7 + core * 0.9 + n * 0.35) * pulse;
    
    // Color mapping (Hot white core fading out to orange-gold and red sparks)
    vec3 base_color = u_color; // E.g., (1.0, 0.45, 0.08)
    vec3 spark_color = vec3(1.0, 0.1, 0.0);
    vec3 center_color = vec3(1.0, 0.9, 0.7);
    
    vec3 final_rgb = mix(spark_color, base_color, smoothstep(0.1, 0.6, intensity));
    final_rgb = mix(final_rgb, center_color, smoothstep(0.7, 1.0, intensity));
    
    // Fade out towards the edges
    float alpha = intensity * (1.0 - smoothstep(0.7, 1.0, dist));
    
    frag_color = vec4(final_rgb, alpha);
}
