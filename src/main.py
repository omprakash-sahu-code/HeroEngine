import os
import sys
import numpy as np
import moderngl

from src.engine.utils.config import load_config
from src.engine.utils.logger import setup_logger
from src.engine.rendering.window import Window
from src.engine.rendering.renderer import Renderer
from src.engine.rendering.shader import ShaderProgram
from src.engine.rendering.texture import Texture2D
from src.engine.vision.camera import CameraCapture
from src.engine.vision.hands.detector import HandDetector
from src.engine.core.monitor import PerformanceMonitor
from src.engine.core.input_manager import InputManager
from src.engine.core.engine import ModuleManager
from src.engine.rendering.post_processing.pipeline import PostProcessingPipeline
import time

logger = setup_logger("Main")

def main():
    logger.info("Initializing HeroEngine Core...")
    
    # 1. Load Configurations
    config_path = os.path.join(os.path.dirname(__file__), "..", "config", "default.yaml")
    config_path = os.path.abspath(config_path)
    
    try:
        config = load_config(config_path)
        logger.info(f"Loaded config from {config_path}")
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        sys.exit(1)

    # 2. Initialize GLFW Window
    display_config = config.get("display", {})
    window = Window(display_config)
    logger.info(f"Window initialized: {window.width}x{window.height}")

    # 3. Initialize ModernGL Renderer Context
    try:
        limit = config.get("rendering", {}).get("particle_limit", 5000)
        renderer = Renderer(particle_limit=limit, config=config)
        ctx = renderer.ctx
    except Exception as e:
        logger.critical(f"Failed to boot renderer: {e}")
        window.close()
        sys.exit(1)

    # Initialize Post-Processing Pipeline
    try:
        pipeline = PostProcessingPipeline(ctx, window.width, window.height, config)
    except Exception as e:
        logger.critical(f"Failed to initialize post-processing pipeline: {e}")
        window.close()
        sys.exit(1)

    # 4. Initialize Asynchronous Vision Pipeline (Camera Source + MediaPipe Detector)
    from src.engine.vision import CameraCapture, HandDetector, VisionPipeline
    camera_config = config.get("camera", {})
    tracking_config = config.get("tracking", {}).get("hands", {})
    
    camera = CameraCapture(camera_config)
    detector = HandDetector(tracking_config)
    vision_pipeline = VisionPipeline(camera, detector)
    if not vision_pipeline.start():
        logger.critical("Failed to start asynchronous vision pipeline.")
        window.close()
        sys.exit(1)

    # 6. Initialize Performance Monitor
    monitor = PerformanceMonitor()
    
    # Initialize Input Manager
    input_manager = InputManager(config)

    # Initialize Active Hero Module Discovery, Loading, & Lifecycle Management
    from src.engine.core.module_registry import ModuleRegistry
    from src.engine.core.module_loader import ModuleLoader
    from src.engine.core.module_manager import ModuleManager

    modules_dir = os.path.join(os.path.dirname(__file__), "modules")
    registry = ModuleRegistry(modules_dir)
    registry.discover()

    loader = ModuleLoader(registry)
    module_manager = ModuleManager(registry, loader)
    
    active_module_name = config.get("module", {}).get("active", "sorcerer")
    module_manager.switch_module(active_module_name, config)

    # Register hotkey callbacks for dynamic module cycling (TAB / SHIFT+TAB) and code hot-reloading (R)
    import glfw
    def on_key(key, scancode, action, mods):
        if action == glfw.PRESS:
            if key == glfw.KEY_TAB:
                forward = not bool(mods & glfw.MOD_SHIFT)
                module_manager.cycle_module(forward=forward, config=config)
            elif key == glfw.KEY_R:
                module_manager.reload_active(config=config)

    window.register_key_callback(on_key)

    # 7. Bind resize callback
    def on_resize(w, h):
        renderer.set_viewport(0, 0, w, h)
        pipeline.resize(w, h)
    window.register_resize_callback(on_resize)
    renderer.set_viewport(0, 0, window.width, window.height)

    # 8. Create OpenGL texture target matching webcam resolution
    logger.info(f"Creating GPU texture target size: {camera.width}x{camera.height}")
    camera_texture = Texture2D(ctx, camera.width, camera.height, components=3)

    # 9. Load Background Shaders
    shader_dir = os.path.join(os.path.dirname(__file__), "engine", "rendering", "shaders")
    vert_shader_path = os.path.join(shader_dir, "background.vert")
    frag_shader_path = os.path.join(shader_dir, "background.frag")
    
    try:
        bg_shader = ShaderProgram(ctx, vert_shader_path, frag_shader_path)
    except Exception as e:
        logger.critical(f"Failed to compile background shaders: {e}")
        vision_pipeline.stop()
        window.close()
        sys.exit(1)

    # 10. Setup Full-Screen Quad geometry (Selfie-Mirrored Texture mapping)
    quad_vertices = np.array([
        # position (x, y), texture coord (u, v) (Mirrored U coord to behave like a mirror, flipped V to render upright)
        -1.0, -1.0,  1.0, 0.0, # Bottom-Left
         1.0, -1.0,  0.0, 0.0, # Bottom-Right
        -1.0,  1.0,  1.0, 1.0, # Top-Left
        
        -1.0,  1.0,  1.0, 1.0, # Top-Left
         1.0, -1.0,  0.0, 0.0, # Bottom-Right
         1.0,  1.0,  0.0, 1.0, # Top-Right
    ], dtype='f4')

    vbo = ctx.buffer(quad_vertices.tobytes())
    vao = ctx.vertex_array(
        bg_shader.program,
        [
            (vbo, '2f 2f', 'in_position', 'in_texcoord')
        ]
    )

    frame_count = 0
    logger.info("Starting Phase 1.2 primary render frame loop.")

    # 11. Core Event Loop
    while not window.should_close():
        # A. Track tick duration
        dt = monitor.tick()
        active_module = module_manager.active_module
        
        # B. Run active module simulation updates (sparks decay, timers)
        if active_module:
            active_module.update(dt)
        
        # C. Read non-blocking VisionResult packet from asynchronous pipeline
        vision_result = vision_pipeline.get_latest_result()
        frame = vision_result.frame if vision_result else None
        hands_data = list(vision_result.hands_data) if vision_result else []
        
        if frame is not None:
            # Feed raw tracking results into InputManager
            input_manager.update(hands_data)
            
            # Feed tracking states to active module
            if active_module:
                active_module.process_input(input_manager.get_hands())
            
            # Print hand details periodically to verify tracking and gesture state
            active_hands = input_manager.get_hands()
            if active_hands and frame_count % 90 == 0:
                for label, hand in active_hands.items():
                    # Check for circular patterns too
                    is_circular, rad, coverage = input_manager.check_circular_motion(label)
                    circ_str = f" | Circle: True (R:{rad:.2f}, Cov:{coverage:.1f})" if is_circular else ""
                    logger.info(
                        f"Hand: {label} | Gesture: {hand.gesture}{circ_str} | "
                        f"Centroid: ({hand.centroid[0]:.2f}, {hand.centroid[1]:.2f}) | "
                        f"Pinch Dist: {hand.pinch_distance:.2f} | "
                        f"Vel: ({hand.velocity[0]:.2f}, {hand.velocity[1]:.2f})"
                    )

            # D. Upload Frame to GPU Texture
            monitor.start_timer("texture_upload")
            # Raw cv2 images are contiguous ndarrays
            camera_texture.write(frame.tobytes())
            monitor.stop_timer("texture_upload")

        # E. Begin Post-Processing Pass (binds offscreen scene FBO)
        pipeline.begin()

        # Clear buffer
        renderer.clear()

        # F. Draw Full-Screen Camera Background Feed
        if frame is not None:
            monitor.start_timer("render_background")
            camera_texture.use(0)
            bg_shader.set_uniform("u_texture", 0)
            vao.render(moderngl.TRIANGLES)
            monitor.stop_timer("render_background")
            
            # G. Draw Hero Module spell effect requests
            if active_module:
                monitor.start_timer("render_effects")
                effect_requests = active_module.get_render_requests()
                aspect = window.width / window.height if window.height > 0 else 1.777
                current_time = time.perf_counter()
                renderer.draw_effects(effect_requests, aspect, current_time)
                monitor.stop_timer("render_effects")

        # H. End Post-Processing Pass (restores screen FBO, runs threshold, blur, bloom blend)
        monitor.start_timer("post_processing")
        pipeline.end()
        monitor.stop_timer("post_processing")

        # G. Display Performance Metrics periodically
        frame_count += 1
        if frame_count % 90 == 0:
            monitor.log_metrics()

        # H. Refresh window
        window.swap_buffers()
        window.poll_events()

    # 12. Shutdown and cleanup
    logger.info("Cleaning up resources...")
    if active_module:
        active_module.release()
        
    # Release post-processing resources
    pipeline.release()
        
    # Release renderer GPU resources
    renderer.release()
    
    vao.release()
    vbo.release()
    bg_shader.release()
    camera_texture.release()
    vision_pipeline.stop()
    window.close()
    logger.info("Shutdown completed successfully.")

if __name__ == "__main__":
    main()
