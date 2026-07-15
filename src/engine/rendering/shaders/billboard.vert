#version 330 core
in vec2 in_position;
in vec2 in_texcoord;

out vec2 v_texcoord;
out vec2 v_local_pos;

uniform vec2 u_center;
uniform float u_radius;
uniform float u_aspect;
uniform float u_rotation;

void main() {
    v_texcoord = in_texcoord;
    v_local_pos = in_position;
    
    vec2 pos = in_position;
    if (u_rotation != 0.0) {
        float s = sin(u_rotation);
        float c = cos(u_rotation);
        pos = vec2(
            in_position.x * c - in_position.y * s,
            in_position.x * s + in_position.y * c
        );
    }
    
    // Apply aspect ratio scale correction (correct vertical stretching on wide viewports)
    vec2 offset = pos * u_radius * vec2(1.0, u_aspect);
    gl_Position = vec4(u_center + offset, 0.0, 1.0);
}
