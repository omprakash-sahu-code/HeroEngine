#version 330 core
in vec2 in_quad_pos;
in vec2 in_birth_pos;
in vec2 in_birth_vel;
in float in_birth_time;
in float in_lifetime;
in vec3 in_color;
in float in_simulation_mode;

out vec2 v_texcoord;
out vec4 v_color;

uniform float u_time;
uniform float u_aspect;

void main() {
    float age = u_time - in_birth_time;
    
    if (age < 0.0 || age > in_lifetime) {
        // Discard instance by moving it off-screen
        gl_Position = vec4(-999.0, -999.0, 0.0, 1.0);
        v_color = vec4(0.0);
        v_texcoord = vec2(0.0);
        return;
    }
    
    vec2 pos;
    float progress = age / in_lifetime;
    
    // Choose simulation behavior based on motion mode
    if (in_simulation_mode > 0.5) {
        // SPIRAL MODE: Inward spiral vortex (implosion)
        // radius decays from a max bounds to 0 at completion
        float start_radius = 0.32;
        float r = start_radius * (1.0 - progress);
        
        // velocity X is hijacked to store the randomized birth start angle
        // angular velocity speed is 13.0 radians/sec
        float theta = in_birth_vel.x + 13.0 * age;
        pos = in_birth_pos + vec2(r * cos(theta), r * sin(theta) * u_aspect);
    } else {
        // BALLISTIC MODE: Standard outward sparks with gravity and air drag deceleration
        // s = v0 * (1.0 - exp(-drag * t)) / drag
        float drag = 1.25;
        vec2 displacement = in_birth_vel * (1.0 - exp(-drag * age)) / drag;
        pos = in_birth_pos + displacement;
        
        // Gravity pull (sparks drift downwards over time)
        pos.y -= 0.16 * age * age;
    }
    
    // Linear scale decay as particle ages
    float size = 0.035 * (1.0 - progress);
    
    // Project local quad coordinates onto NDC space (correcting aspect ratio)
    vec2 vertex_pos = pos + in_quad_pos * size * vec2(1.0, u_aspect);
    
    gl_Position = vec4(vertex_pos, 0.0, 1.0);
    v_texcoord = in_quad_pos + vec2(0.5); // Translate coordinate space [-0.5, 0.5] -> [0.0, 1.0]
    
    // Fade color alpha over lifespan
    float alpha = 1.0 - progress;
    v_color = vec4(in_color, alpha);
}
