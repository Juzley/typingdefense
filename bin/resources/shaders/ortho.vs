#version 140
#extension GL_ARB_explicit_attrib_location : require

uniform vec2 screenDimensions;

layout (location = 0) in vec2 Position;
layout (location = 1) in vec2 TexCoord;

out vec2 texCoords;

void main()
{
    gl_Position = vec4((Position.x * 2.0f / screenDimensions.x) - 1.0f, 
                       (Position.y * 2.0f / screenDimensions.y) - 1.0f,
                       0.0, 1.0f);
    texCoords = TexCoord;
}
