#version 140
#extension GL_ARB_explicit_attrib_location : require

layout (location = 0) in vec2 Position;
layout (location = 1) in vec2 TexCoord;

out vec2 texCoords;

void main()
{
    gl_Position = vec4(Position.x, Position.y, 0.0, 1.0f);
    texCoords = TexCoord;
}
