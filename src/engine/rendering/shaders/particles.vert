#version 330 core
in vec2 in_position;
in vec4 in_color;

out vec4 v_color;

uniform float u_base_size;

void main() {
    v_color = in_color;
    
    // Scale particle point size dynamically: shrinks as it ages (alpha decay)
    gl_PointSize = u_base_size * in_color.a;
    
    gl_Position = vec4(in_position, 0.0, 1.0);
}
