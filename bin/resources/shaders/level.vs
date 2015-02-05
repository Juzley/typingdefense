#version 140
#extension GL_ARB_explicit_attrib_location : require

uniform mat4 transMatrix;
layout (location = 0) in vec3 Position;

void main()
{
    gl_Position = transMatrix * vec4(Position, 1.0);
}
