#version 140

uniform sampler2D texUnit;
uniform vec3 inColour;
in vec2 texCoords;
out vec4 outColour;

void main()
{
    outColour = texture2D(texUnit, texCoords.st);
    outColour.x = inColour.x;
    outColour.y = inColour.y;
    outColour.z = inColour.z;
}
