#version 140
#extension GL_ARB_explicit_attrib_location : require

uniform mat4 transMatrix;
layout (location = 0) in vec3 vert_position;
layout (location = 1) in vec4 vert_colour;
out vec4 frag_colour;

void main()
{
    gl_Position = transMatrix * vec4(vert_position, 1.0f);
    frag_colour = vert_colour;
}
