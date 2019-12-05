
header = '''
#ifdef GL_ES
    precision highp float;
#endif

/* Outputs from the vertex shader */
varying vec4 frag_color;
varying vec2 tex_coord0;

/* uniform texture samplers */
uniform sampler2D texture0;

uniform mat4 frag_modelview_mat;

uniform int daltonize;
uniform int transformation;  // deuteranopia, protanopia or tritanopia
uniform int linearize;
uniform float transform_cutoff;
uniform int colorimetric_modification;

'''

shader_monochrome = header + '''
void main(void)
{

    vec3 colour = texture2D(texture0, tex_coord0).xyz;

    float shade = length(colour) / sqrt(3.0);

    gl_FragColor = vec4(shade, shade, shade, 1.0);
}
'''

shader_normal = header + '''
void main(void)
{

    vec3 colour = texture2D(texture0, tex_coord0).xyz;

    gl_FragColor = vec4(colour, 1.0);
}
'''

## Possible transformations:
## 0: none
## 1: protanopia (red)
## 2: deuteranopia (green)
## 3: tritanopia (blue)
## 4: monochromacy

shader_chromaticity = header + '''
void main(void)
{
    vec3 input_rgb = texture2D(texture0, tex_coord0).xyz;

    float divisor = (input_rgb.x + input_rgb.y + input_rgb.z);

    if (divisor < 0.00001f)
    {
        divisor = 1.0f;
    }

    vec3 output_rgb = input_rgb / (input_rgb.x + input_rgb.y + input_rgb.z);

    gl_FragColor = vec4(output_rgb, 1.0);

}
'''

shader_colour_blindness = header + '''
void main(void)
{

    // matrix to convert from RGB to LMS colour space
    mat3 rgb_to_lms = mat3(17.8824, 3.45565, 0.0299566,
                           43.5161, 27.1554, 0.184309,
                           4.11935, 3.86714, 1.46709);

    // inverse colour transformation matrix
    mat3 lms_to_rgb = mat3(0.0809444, -0.010248533, -0.000365297,
                           -0.130504, 0.05401932666, -0.00412161,
                           0.116721, -0.113614708, 0.6935114);

    // get the input colour (this comes from the camera image texture)
    vec3 input_rgb = texture2D(texture0, tex_coord0).xyz;

    if (linearize == 1) {
        input_rgb = vec3(pow(input_rgb.x, 2.2), pow(input_rgb.y, 2.2), pow(input_rgb.z, 2.2));
    }

    if (transformation == 1) {
        input_rgb = 0.992052 * input_rgb + 0.003974;
    } else if (transformation == 2) {
        input_rgb = 0.957237 * input_rgb + 0.0213814;
    }

    // Modify the chromaticity
    float denominator = input_rgb.x + input_rgb.y + input_rgb.z;
    float C_x = input_rgb.x / denominator;
    float C_y = input_rgb.y / denominator;
    float C_x_2 = (1.0271 * C_x - 0.00008 * C_y - 0.00009) / (0.03845 * C_x + 0.01496 * C_y + 1.0);
    float C_y_2 = (0.00376 * C_x + 1.0072 * C_y + 0.00764) / (0.03845 * C_x + 0.01496 * C_y + 1.0);

    if (colorimetric_modification == 1) {
        input_rgb = vec3(denominator * C_x_2, denominator * C_y_2, denominator * (1.0 - C_x_2 - C_y_2));
    }

    // convert the RGB input colour to LMS colour space
    vec3 input_lms = rgb_to_lms * input_rgb;

    mat3 correction_matrix;
    mat3 error_matrix;
    if (transformation == 0) {
        // no transformation, identity matrix
        correction_matrix = mat3(1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0);
        error_matrix = mat3(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0);
    } else if (transformation == 1) {
        // protanopia, remove red (L component)
        correction_matrix = mat3(0.0, 0.0, 0.0,
                                 2.02344, 1.0, 0.0,
                                -2.52581, 0.0, 1.0);
//        correction_matrix = mat3(0.0, 0.0, 0.0,
//                                 0.0 , 1.0, 0.0,
//                                 0.0, 0.0, 1.0);
        error_matrix = mat3(0.0, 0.7, 0.7, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0);
    } else if (transformation == 2) {
        // deuteranopia, remove green (M component)
        correction_matrix = mat3(1.0, 0.494207, 0.0,
                                 0.0, 0.0, 0.0,
                                 0.0, 1.24827, 1.0);
//        correction_matrix = mat3(1.0, 0.0, 0.0,
//                                 0.0 , 0.0, 0.0,
//                                 0.0, 0.0, 1.0);
        error_matrix = mat3(1.0, 0.0, 0.0, 0.7, 0.0, 0.7, 0.0, 0.0, 1.0);
    } else if (transformation == 3) {
        // tritanopia, remove blue (S component)
        correction_matrix = mat3(1.0, 0.0, -0.012245,
                                 0.0, 1.0, 0.072035,
                                 0.0, 0.0, 0.0);
//        correction_matrix = mat3(1.0, 0.0, 0.0,
//                                 0.0 , 1.0, 0.0,
//                                 0.0, 0.0, 0.0);
        error_matrix = mat3(1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.7, 0.7, 0.0);
    }

    // convert the input colour to an output colour with colour-blindness
    vec3 colour_blind_lms = correction_matrix * input_lms;

    // convert the output colour back to RGB colour space
    vec3 colour_blind_rgb = lms_to_rgb * colour_blind_lms;

    vec3 error = input_rgb - colour_blind_rgb;

    vec3 error_term = error_matrix * error;

    vec3 daltonized_rgb = error_term + input_rgb;

    vec3 output_rgb;
    if (daltonize == 1) {
        output_rgb = daltonized_rgb;
    } else {
        output_rgb = colour_blind_rgb;
    }

    if (linearize == 1) {
        output_rgb = vec3(pow(output_rgb.x, 1.0 / 2.2), pow(output_rgb.y, 1.0 / 2.2), pow(output_rgb.z, 1.0 / 2.2));
        input_rgb = vec3(pow(input_rgb.x, 1.0 / 2.2), pow(input_rgb.y, 1.0 / 2.2), pow(input_rgb.z, 1.0 / 2.2));
    }

    if (gl_FragCoord.x > transform_cutoff) {
        output_rgb = input_rgb;
    }


    // gl_FragColor is the final output colour for this pixel
    gl_FragColor = vec4(output_rgb, 1.0);
}
'''
