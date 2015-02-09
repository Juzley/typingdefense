#version 140

uniform vec4 colourIn;
out vec4 colourOut; 

void main()
{
    // The tile coords are stored in the 'colour' from the vertex shader
    // The q and r coordinates are taken from the input colour r and g and
    // output in the output colour r and g. Output 1 for the b, so we can
    // distinguish from a 'background' pixel - the buffer will be cleared
    // to black before doing the picking draw.
    colourOut = vec4(colourIn.x, colourIn.y, 1.0f, 1.0f);
}
