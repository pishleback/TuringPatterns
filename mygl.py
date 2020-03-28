import OpenGL.GL as gl
import ctypes
import numpy as np
import pygame





class Texture():
    def __init__(self, width, height, data = None, interp = True, float_tex = False):
        tex_id = gl.glGenTextures(1)
        gl.glActiveTexture(gl.GL_TEXTURE0 + tex_id)
        
        gl.glBindTexture(gl.GL_TEXTURE_2D, tex_id)
        gl.glEnable(gl.GL_TEXTURE_2D)

        gl.glPixelStorei(gl.GL_UNPACK_ALIGNMENT, 1)

        if float_tex:
            gl.glTexImage2D(gl.GL_TEXTURE_2D,
                            0,
                            gl.GL_RGBA16F,
                            width,
                            height,
                            0,
                            gl.GL_RGBA,
                            gl.GL_FLOAT,
                            data)
        else:
            gl.glTexImage2D(gl.GL_TEXTURE_2D,
                            0,
                            gl.GL_RGBA,
                            width,
                            height,
                            0,
                            gl.GL_RGBA,
                            gl.GL_UNSIGNED_BYTE,
                            data)

        gl.glTexParameterf(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_MIRRORED_REPEAT)
        gl.glTexParameterf(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_MIRRORED_REPEAT)
        gl.glTexParameterf(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR if interp else gl.GL_NEAREST)
        gl.glTexParameterf(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR if interp else gl.GL_NEAREST)

        self.width = width
        self.height = height
        self.tex_id = tex_id
        self.bound = False

    def bind(self):
        self.bound = True
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.tex_id)

    def unbind(self):
        self.bound = False
        gl.glBindTexture(gl.GL_TEXTURE_2D, 0)

    def get_id(self):
        return self.tex_id


def ImageTexture(path, interp = True):
    textureSurface = pygame.image.load(path)
    textureData = pygame.image.tostring(textureSurface, "RGBA", 1)
    width = textureSurface.get_width()
    height = textureSurface.get_height()
    return Texture(width, height, textureData, interp)




class FrameBuffer():
    def __init__(self):
        self.fbo_id = gl.glGenFramebuffers(1)
        self.bound = False

    def bind(self, rect):
        self.bound = True
        gl.glBindFramebuffer(gl.GL_DRAW_FRAMEBUFFER, self.fbo_id)
        gl.glViewport(*rect)

    def unbind(self, rect):
        self.bound = False
        gl.glBindFramebuffer(gl.GL_DRAW_FRAMEBUFFER, 0)
        gl.glViewport(*rect)

    def add_texture(self, texture):
        assert self.bound
        gl.glFramebufferTexture2D(gl.GL_FRAMEBUFFER,
                                  gl.GL_COLOR_ATTACHMENT0, #make this changable
                                  gl.GL_TEXTURE_2D,
                                  texture.get_id(),
                                  0)




class RawModel():
    def __init__(self, vao_id, indices, all_data, prim_mode):
        self.vao_id = vao_id
        self.indices = indices
        self.all_data = all_data
        self.prim_mode = prim_mode

    def render(self):
        #bind stuff
        gl.glBindVertexArray(self.vao_id)
        for loc in self.all_data:
            gl.glEnableVertexAttribArray(loc)
        #draw
        gl.glDrawElements(self.prim_mode, self.indices.size, gl.GL_UNSIGNED_INT, ctypes.c_void_p(0))
        #unbind stuff
        for loc in self.all_data:
            gl.glDisableVertexAttribArray(loc)
        gl.glBindVertexArray(0)



def load_model(all_data, indices, prim_mode):
    indices = np.array(indices)
    all_data = {loc : np.array(all_data[loc]) for loc in all_data}
    #data is a dict of {loc : array}

    
    #NOTE: im not sure why I unbind the data vbos but not the index ones?

    #create vao for the data
    vao_id = gl.glGenVertexArrays(1)
    #bind vao
    gl.glBindVertexArray(vao_id)

    #INDEX STUFF
    #create vbo for indices
    vbo_id = gl.glGenBuffers(1)
    #bind indices
    gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, vbo_id)
    #write to the indices
    gl.glBufferData(gl.GL_ELEMENT_ARRAY_BUFFER, indices.nbytes, indices, gl.GL_STATIC_DRAW)
##    #unbind indices
##    gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, 0)

    #DATA STUFF
    assert len(set([len(all_data[loc]) for loc in all_data])) == 1
    for loc in all_data:
        data = all_data[loc].astype(np.float32)
        #create vbo
        vbo_id = gl.glGenBuffers(1)
        #bind vbo
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, vbo_id)
        #static draw means we dont edit it later
        gl.glBufferData(gl.GL_ARRAY_BUFFER, data.nbytes, data, gl.GL_STATIC_DRAW)

        stride = data.strides[0]
        gl.glVertexAttribPointer(loc, data.shape[1], gl.GL_FLOAT, gl.GL_FALSE, stride, ctypes.c_void_p(0))

        #unbind vbo
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, 0)

    #unbind vao
    gl.glBindVertexArray(0)
    
    return RawModel(vao_id, indices, all_data, prim_mode)

    


class Program():
    def __init__(self, vertex_code, geometry_code, fragment_code):
        program  = gl.glCreateProgram()
        vertex   = gl.glCreateShader(gl.GL_VERTEX_SHADER)
        if geometry_code != None:
            geometry = gl.glCreateShader(gl.GL_GEOMETRY_SHADER)
        fragment = gl.glCreateShader(gl.GL_FRAGMENT_SHADER)

        # Set shaders source
        gl.glShaderSource(vertex, vertex_code)
        if geometry_code != None:
            gl.glShaderSource(geometry, geometry_code)
        gl.glShaderSource(fragment, fragment_code)

        # Compile shaders
        gl.glCompileShader(vertex)
        if not gl.glGetShaderiv(vertex, gl.GL_COMPILE_STATUS):
            error = gl.glGetShaderInfoLog(vertex).decode()
            print(error)
            raise RuntimeError("Vertex shader compilation error")

        if geometry_code != None:
            gl.glCompileShader(geometry)
            if not gl.glGetShaderiv(geometry, gl.GL_COMPILE_STATUS):
                error = gl.glGetShaderInfoLog(geometry).decode()
                print(error)
                raise RuntimeError("Geometry shader compilation error")

        gl.glCompileShader(fragment)
        if not gl.glGetShaderiv(fragment, gl.GL_COMPILE_STATUS):
            error = gl.glGetShaderInfoLog(fragment).decode()
            print(error)
            raise RuntimeError("Fragment shader compilation error")

        gl.glAttachShader(program, vertex)
        if geometry_code != None:
            gl.glAttachShader(program, geometry)
        gl.glAttachShader(program, fragment)
        gl.glLinkProgram(program)

        if not gl.glGetProgramiv(program, gl.GL_LINK_STATUS):
            print(gl.glGetProgramInfoLog(program))
            raise RuntimeError('Linking error')

        #dont need the shader files now
        gl.glDetachShader(program, vertex)
        if geometry_code != None:
            gl.glDetachShader(program, geometry)
        gl.glDetachShader(program, fragment)

        self.program = program


    def get_attrib_loc(self, name):
        loc = gl.glGetAttribLocation(self.program, name)
        if loc != -1:
            return loc
        else:
            raise Exception("Attrib " + name + " not found.")


    def use(self):
        gl.glUseProgram(self.program)
    

    def set_uniform(self, name, value, kind):
        gl.glUseProgram(self.program)
        #send uniform value
        loc = gl.glGetUniformLocation(self.program, name)
        if loc != -1:
            if kind == gl.glUniformMatrix4fv:
                gl.glUniformMatrix4fv(loc, 1, gl.GL_TRUE, np.ascontiguousarray(value))
            else:
                kind(loc, *value)
        else:
            print("Warning: uniform " + str(name) + " not found")
    def set_texture_uniform(self, name, texture):
        assert type(texture) == Texture
        self.set_uniform(name, [texture.get_id()], gl.glUniform1i)


















