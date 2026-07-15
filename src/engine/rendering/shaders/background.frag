#version 330 core

in vec2 v_texcoord;
out vec4 fragColor;

uniform sampler2D u_texture;

void main() {
    // Perform BGR to RGB channel swapping on the GPU for maximum performance
    fragColor = vec4(texture(u_texture, v_texcoord).bgr, 1.0);
}
