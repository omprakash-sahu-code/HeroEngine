#version 330 core
in vec2 v_texcoord;
out vec4 frag_color;

uniform sampler2D u_texture;
uniform bool u_horizontal;
uniform float u_texel_size;

// Gaussian blur kernel weights (9-tap)
const float weight[5] = float[](0.2270270270, 0.1945945946, 0.1216216216, 0.0540540541, 0.0162162162);

void main() {
    vec2 offset = u_horizontal ? vec2(u_texel_size, 0.0) : vec2(0.0, u_texel_size);
    vec3 result = texture(u_texture, v_texcoord).rgb * weight[0];
    
    for (int i = 1; i < 5; ++i) {
        result += texture(u_texture, v_texcoord + offset * float(i)).rgb * weight[i];
        result += texture(u_texture, v_texcoord - offset * float(i)).rgb * weight[i];
    }
    
    frag_color = vec4(result, 1.0);
}
