import mygl
import pygame
import OpenGL.GL as gl
import numpy as np
import math
import os
import time







class Feedback():
    VERTEX_CODE = """
    #version 410
    in vec2 scr_pos;
    in vec2 vert_uv_pos;
    out vec2 uv_pos;
    
    void main() {
        gl_Position = vec4(scr_pos, 0.0, 1.0);
        uv_pos = vert_uv_pos;
    }
    """

    ID_FRAG_CODE = """
    #version 410
    in vec2 uv_pos;
    uniform sampler2D tex;
    uniform vec2 size;
    
    out vec4 colour;
    
    void main() {
        colour = texture(tex, uv_pos);
    }
    """
    
    def __init__(self, size, fragment_tick_code, fragment_render_code):
        tex_data = mygl.Texture(*size, interp = True, float_tex = True)
        fbo_data = mygl.FrameBuffer()
        fbo_data.bind([0, 0, size[0], size[1]])
        fbo_data.add_texture(tex_data)
        fbo_data.unbind([0, 0, size[0], size[1]])

        tex_loop = mygl.Texture(*size, interp = True, float_tex = True)
        fbo_loop = mygl.FrameBuffer()
        fbo_loop.bind([0, 0, size[0], size[1]])
        fbo_loop.add_texture(tex_loop)
        fbo_loop.unbind([0, 0, size[0], size[1]])

        loop_prog = mygl.Program(Feedback.VERTEX_CODE, None, Feedback.ID_FRAG_CODE)
        loop_prog.set_texture_uniform("tex", tex_data)
        loop_prog_render_quad = mygl.load_model({loop_prog.get_attrib_loc("scr_pos") : [[-1, -1], [1, -1], [1, 1], [-1, 1]],
                                                 loop_prog.get_attrib_loc("vert_uv_pos") : [[0, 0], [1, 0], [1, 1], [0, 1]]},
                                                [0, 1, 2, 2, 0, 3],
                                                gl.GL_TRIANGLES)
        
        calc_prog = mygl.Program(Feedback.VERTEX_CODE, None, fragment_tick_code)
        calc_prog.set_texture_uniform("tex", tex_loop)
        calc_prog_render_quad = mygl.load_model({calc_prog.get_attrib_loc("scr_pos") : [[-1, -1], [1, -1], [1, 1], [-1, 1]],
                                                 calc_prog.get_attrib_loc("vert_uv_pos") : [[0, 0], [1, 0], [1, 1], [0, 1]]},
                                                [0, 1, 2, 2, 0, 3],
                                                gl.GL_TRIANGLES)
        calc_prog.set_uniform("size", size, gl.glUniform2f)

        render_prog = mygl.Program(Feedback.VERTEX_CODE, None, fragment_render_code)
        render_prog.set_texture_uniform("tex", tex_data)
        render_prog_render_quad = mygl.load_model({render_prog.get_attrib_loc("scr_pos") : [[-1, -1], [1, -1], [1, 1], [-1, 1]],
                                                   render_prog.get_attrib_loc("vert_uv_pos") : [[0, 0], [1, 0], [1, 1], [0, 1]]},
                                                  [0, 1, 2, 2, 0, 3],
                                                  gl.GL_TRIANGLES)
        render_prog.set_uniform("size", size, gl.glUniform2f)

        self.size = size
        self.fbo_data = fbo_data
        self.fbo_loop = fbo_loop
        self.loop_prog = loop_prog
        self.calc_prog = calc_prog
        self.render_prog = render_prog
        self.loop_prog_render_quad = loop_prog_render_quad
        self.calc_prog_render_quad = calc_prog_render_quad
        self.render_prog_render_quad = render_prog_render_quad

    def tick(self):
        rect = [0, 0, self.size[0], self.size[1]]
        
        self.fbo_loop.bind(rect)
        self.loop_prog.use()
        self.loop_prog_render_quad.render()

        self.fbo_data.bind(rect)
        self.calc_prog.use()
        self.calc_prog_render_quad.render()

        self.fbo_loop.unbind(rect)

    def render(self):
        self.render_prog.use()
        self.render_prog_render_quad.render()










def run():
    pygame.init()
    screen = pygame.display.set_mode((1600, 1000), pygame.DOUBLEBUF | pygame.OPENGL)
    size = screen.get_size()


    tick_frag_code = """
    #version 410
    in vec2 uv_pos;
    uniform sampler2D tex;
    uniform vec2 size;
    uniform vec2 draw_center;
    uniform float draw_radius;
    uniform vec4 draw_value;
    uniform vec2 start;
    uniform vec2 end;
    uniform float scale;
    out vec4 colour;


    void laplace(out vec4 ans, float x, float y, float dx, float dy, sampler2D tex) {
        ans = -texture(tex, uv_pos) + 0.2 * texture(tex, vec2(x + dx, y)) + 0.2 * texture(tex, vec2(x - dx, y)) + 0.2 * texture(tex, vec2(x, y + dy)) + 0.2 * texture(tex, vec2(x, y - dy))
               + 0.05 * texture(tex, vec2(x + dx, y + dy)) + 0.05 * texture(tex, vec2(x - dx, y - dy)) + 0.05 * texture(tex, vec2(x - dy, y + dy)) + 0.05 * texture(tex, vec2(x + dy, y - dy));
    }
    
    void main() {
        float x = uv_pos.x;
        float y = uv_pos.y;
        
        float d = 1 / scale;
        float dx = 1 / size.x;
        float dy = 1 / size.y;
        
        if ( pow((x * size[0] - draw_center[0]), 2) + pow((y * size[1] - draw_center[1]), 2) < pow(draw_radius, 2) ) {
            colour = draw_value;
        } else {

            float A;
            float B;
            float nA;
            float nB;
            float La;
            float Lb;

            float Da = scale * 1.0;
            float Db = scale * 0.3;
            float k = start[0] + x * (end[0] - start[0]);
            float f = start[1] + y * (end[1] - start[1]);

            A = texture(tex, vec2(x, y))[0];
            B = texture(tex, vec2(x, y))[1];

            vec4 L;
            laplace(L, x, y, dx, dy, tex);
            La = L[0];
            Lb = L[1];
            
            nA = A + d * (Da * La - A * B * B + f * (1 - A));
            nB = B + d * (Db * Lb + A * B * B - (k + f) * B);

            colour = vec4(0.0, 0.0, 0.0, 0.0);
            colour[0] = min(max(nA, 0), 1);
            colour[1] = min(max(nB, 0), 1);
        }
    }
    """
    

    render_frag_code = """
    #version 410
    in vec2 uv_pos;
    uniform sampler2D tex;
    uniform sampler2D pal;
    uniform float scale;
    uniform vec2 size;
    uniform vec3 light;
    
    out vec4 colour;
    
    void main() {
        float mult = 200;
    
        float dx = 1 / size.x;
        float dy = 1 / size.y;
    
        vec4 values = texture(tex, uv_pos);

        vec3 normal = vec3((texture(tex, uv_pos + vec2(dx, 0))[0] - texture(tex, uv_pos - vec2(dx, 0))[0]) / (2 * mult * dx),
                           (texture(tex, uv_pos + vec2(0, dy))[0] - texture(tex, uv_pos - vec2(0, dy))[0]) / (2 * mult * dy),
                            -1 / sqrt(scale));

        normal = normal / length(normal);


        vec3 light_dir = light; light_dir = light_dir / length(light_dir);
        vec3 light_refl_dir = light_dir + 2 * (dot(normal, light_dir) * normal - light_dir);

        float oof = 0;
        
        //blinn phong lighting
        oof += pow(abs(light_refl_dir.z), 100);
        
        //diffuse lighting
        oof += dot(normal.xy, light_dir.xy);
                
        colour = texture(pal, values.xy) + oof;
    }
    """
    

    feedback = Feedback(size, tick_frag_code, render_frag_code)

    pal_tex = mygl.ImageTexture(os.path.join("redif", "palettes", "oof.png"))
    feedback.render_prog.set_texture_uniform("pal", pal_tex)

        
    clock = pygame.time.Clock()

    def convert_inwards(pos):
        side = math.sqrt(size[0] * size[1])
        return [center[i] + scale * 2 * (pos[i] - 0.5 * size[i]) / side for i in [0, 1]]

    center = [0.064, 0.041]
    scale = 0.01
    diff_speed = 1

    light_angle = 2
    light_radius = 0.5
    
    while True:        
        fps = max(clock.get_fps(), 1)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
                
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 4:
                    p1 = convert_inwards(event.pos)
                    scale /= 1.2
                    p2 = convert_inwards(event.pos)
                    center = [center[i] + (p1[i] - p2[i]) for i in [0, 1]]
                if event.button == 5:
                    p1 = convert_inwards(event.pos)
                    scale *= 1.2
                    p2 = convert_inwards(event.pos)
                    center = [center[i] + (p1[i] - p2[i]) for i in [0, 1]]

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    diff_speed *= 1.1
                if event.key == pygame.K_DOWN:
                    diff_speed /= 1.1

        if pygame.key.get_pressed()[pygame.K_w]:
            light_radius += 0.01
        if pygame.key.get_pressed()[pygame.K_s]:
            light_radius -= 0.01
            if light_radius < 0: light_radius = 0
        if pygame.key.get_pressed()[pygame.K_a]:
            light_angle += 0.06
        if pygame.key.get_pressed()[pygame.K_d]:
            light_angle -= 0.06
                
##        gl.glClear(gl.GL_COLOR_BUFFER_BIT)

        if pygame.mouse.get_pressed()[0]:
            pos = pygame.mouse.get_pos()
            feedback.calc_prog.set_uniform("draw_center", [pos[0], size[1] - pos[1]], gl.glUniform2f)
            feedback.calc_prog.set_uniform("draw_radius", [1], gl.glUniform1f)
            feedback.calc_prog.set_uniform("draw_value", [1, 1, 0, 0], gl.glUniform4f)
        elif pygame.mouse.get_pressed()[2]:
            pos = pygame.mouse.get_pos()
            feedback.calc_prog.set_uniform("draw_center", [pos[0], size[1] - pos[1]], gl.glUniform2f)
            feedback.calc_prog.set_uniform("draw_radius", [200], gl.glUniform1f)
            feedback.calc_prog.set_uniform("draw_value", [1, 0, 0, 0], gl.glUniform4f)
        else:
            feedback.calc_prog.set_uniform("draw_radius", [0], gl.glUniform1f)

        feedback.calc_prog.set_uniform("start", convert_inwards([0, size[1]]), gl.glUniform2f)
        feedback.calc_prog.set_uniform("end", convert_inwards([size[0], 0]), gl.glUniform2f)
        feedback.calc_prog.set_uniform("scale", [diff_speed], gl.glUniform1f)

        feedback.render_prog.set_uniform("scale", [diff_speed], gl.glUniform1f)
        feedback.render_prog.set_uniform("light", [light_radius * math.cos(light_angle), light_radius * math.sin(light_angle), -1], gl.glUniform3f)

        for _ in range(20):
            feedback.tick()
        feedback.render()
        
        pygame.display.flip()
        clock.tick(100)
























