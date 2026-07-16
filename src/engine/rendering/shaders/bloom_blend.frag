#version 330 core
in vec2 v_texcoord;
out vec4 frag_color;

uniform sampler2D u_scene_tex;
uniform sampler2D u_bloom_tex;

uniform float u_bloom_intensity;
uniform float u_exposure;
uniform float u_gamma;

void main() {
    vec3 scene_color = texture(u_scene_tex, v_texcoord).rgb;
    vec3 bloom_color = texture(u_bloom_tex, v_texcoord).rgb;
    
    // Additive bloom blending
    vec3 color = scene_color + bloom_color * u_bloom_intensity;
    
    // Exposure-based HDR tone mapping (preserves highlight details)
    vec3 mapped = vec3(1.0) - exp(-color * u_exposure);
    
    // Gamma correction
    mapped = pow(mapped, vec3(1.0 / u_gamma));
    
    frag_color = vec4(mapped, 1.0);
}
