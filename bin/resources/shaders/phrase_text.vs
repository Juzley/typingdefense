#version 140
#extension GL_ARB_explicit_attrib_location : require

uniform mat4 transMatrix;
uniform vec3 origin;
uniform vec2 screenDimensions;

layout (location = 0) in vec2 Position;
layout (location = 1) in vec2 TexCoord;

out vec2 texCoords;

void main()
{
    vec4 project_pos = transMatrix * vec4(origin, 1.0);
    
    // Perspective divide, results in project_pos being in NDC.
    project_pos /= project_pos.w;


    gl_Position = vec4(Position.x / screenDimensions.x + project_pos.x,
                       Position.y / screenDimensions.y + project_pos.y,
                       project_pos.z,
                       1.0);
    texCoords = TexCoord;
}

