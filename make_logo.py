import PIL as pil
import numpy as np

from colorsys import hsv_to_rgb

def make_logo_rect():

    pixels_per_row = 512 // 4

    arr = np.zeros((512, 512, 4))

    arr[:, :, -1] = 0.6

    for row in [0, 2, 3]:
        arr[row * pixels_per_row:(row + 1) * pixels_per_row,:512 // 3] = [1, 0, 0, 1]

    for row in [0, 1, 3]:
        arr[row * pixels_per_row:(row + 1) * pixels_per_row,512 // 3:2*512 // 3] = [0, 1, 0, 1]

    for row in [0, 1, 2]:
        arr[row * pixels_per_row:(row + 1) * pixels_per_row,2*512 // 3:] = [0, 0, 1, 1]

    for row in range(3):
        row += 1
        line_radius = 5
        # arr[row * pixels_per_row - line_radius:row * pixels_per_row + line_radius + 1] *= 0.
        # arr[row * pixels_per_row - line_radius:row * pixels_per_row + line_radius + 1, -1] = 1.
        arr[row * pixels_per_row - line_radius:row * pixels_per_row + line_radius + 1] = [0, 0, 0, 1]

    arr *= 255

    im = pil.Image.fromarray(arr.astype(np.uint8), "RGBA")

    im.save("logo.png")
    return im

def make_logo_hsv():
    arr = np.zeros((512, 512, 4))

    xs, ys = np.meshgrid(np.linspace(-1, 1, 512), np.linspace(-1, 1, 512))

    angles = np.arctan2(ys, xs)
    angles += np.pi
    angles /= 2 * np.pi

    angles += 0.22934
    angles %= 1.

    for i in range(512):
        for j in range(512):
            x = i - 256
            y = j - 256
            dist = np.sqrt(x**2 + y**2)

            angle = angles[i, j]

            if dist > 190.:
                saturation = max(1, dist / 190.)
            else:
                saturation = min(1, dist / 100.)

            arr[i, j] = list(hsv_to_rgb(angle, saturation, 1)) + [1.]

    print(np.min(angles), np.max(angles))

    arr *= 255

    im = pil.Image.fromarray(arr.astype(np.uint8), "RGBA")

    im.save("logo.png")
    return im, arr

if __name__ == "__main__":
    make_logo_hsv()
