#version 330 core
in vec2 v_texcoord;
in vec2 v_local_pos;

out vec4 frag_color;

uniform float u_time;
uniform vec3 u_color; // Default color theme

// Draw concentric ring helper
float draw_ring(float dist, float radius, float thickness) {
    return smoothstep(thickness, 0.0, abs(dist - radius));
}

// Pseudo-noise helper
float hash(float n) { return fract(sin(n) * 43758.5453123); }

void main() {
    float dist = length(v_local_pos);
    
    // Bounds check
    if (dist > 1.0) {
        discard;
    }
    
    float theta = atan(v_local_pos.y, v_local_pos.x);
    
    // Compute magic seal rings
    float r1 = draw_ring(dist, 0.90, 0.015); // Broad outer ring
    float r2 = draw_ring(dist, 0.85, 0.008); // Thin accent outer ring
    float r3 = draw_ring(dist, 0.65, 0.010); // Middle ring
    
    // Dashed runic ring (24 dashes)
    float dash = step(0.0, sin(theta * 24.0 + u_time * 2.0));
    float r4 = draw_ring(dist, 0.73, 0.012) * dash;
    
    // Innermost ring
    float r5 = draw_ring(dist, 0.38, 0.010);
    
    // 8 Spoke Star geometric pattern
    float spoke_dash = step(0.0, sin(theta * 8.0 - u_time * 1.5));
    float star = draw_ring(dist, 0.50, 0.12) * spoke_dash * step(0.38, dist);
    
    // Dynamic noise texture overlay for magic sparks inside the ring
    float spark_noise = fract(sin(dot(v_local_pos.xy * 15.0, vec2(12.9898, 78.233))) * 43758.5453);
    float spark = step(0.97, spark_noise) * (1.0 - smoothstep(0.4, 0.9, dist));
    
    // Center glowing orb core
    float core = exp(-6.0 * dist);
    
    // Combine layers
    float shape = r1 + r2 + r3 + r4 + r5 + star * 0.4 + core * 0.5 + spark * 0.35;
    
    // Pulse animation
    float pulse = 0.9 + 0.1 * sin(u_time * 5.0);
    shape *= pulse;
    
    // Output color (gold/orange with glowing edges)
    vec3 final_rgb = u_color * shape;
    // Boost hot core brightness to white-hot
    final_rgb += vec3(1.0, 0.8, 0.6) * core * 0.6;
    
    float alpha = clamp(shape, 0.0, 1.0) * (1.0 - smoothstep(0.92, 1.0, dist));
    
    frag_color = vec4(final_rgb, alpha);
}
