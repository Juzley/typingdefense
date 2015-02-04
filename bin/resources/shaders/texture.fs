#version 140

uniform sampler2D texUnit;
in vec2 texCoords;
out vec4 outColour;

void main()
{
    outColour = texture2D(texUnit, texCoords.st);
}
