import numpy as np
from PIL import Image, ImageDraw, ImageFont
import math


def image_diff(img1, img2):
    img1 = img1.resize((100, 100))
    img2 = img2.resize((100, 100))

    # Convert images to numpy arrays
    img_arr1 = np.array(img1)
    img_arr2 = np.array(img2)

    # Calculate RMSE
    mse = np.mean((img_arr1 - img_arr2) ** 2)
    rmse = np.sqrt(mse)
    return rmse


class Canvas:
    def __init__(self, width, height, colour=(0, 0, 0, 255)):
        self.width = width
        self.height = height
        self.image = Image.new("RGBA", (self.width, self.height), color=colour)
        self.pixels = self.image.load()
        self.draw = ImageDraw.Draw(self.image)

    def draw_circle(self, xy, radius, colour):
        center = xy
        bounding_box = [
            (center[0] - radius, center[1] - radius),
            (center[0] + radius, center[1] + radius),
        ]
        self.draw.ellipse(bounding_box, fill=colour, width=1)

    def draw_line(self, xy, vector, colour):
        start_point = xy
        end_point = (xy[0] + vector[0], xy[1] + vector[1])
        self.draw.line([start_point, end_point], fill=colour, width=1)

    def draw_rectangle(self, xy, width, height, colour):
        x0 = int(xy[0])
        y0 = int(xy[1])
        x1 = min(self.width, x0 + int(width))
        y1 = min(self.height, y0 + int(height))
        alpha = colour[3] / 255.0
        for x in range(x0, x1):
            for y in range(y0, y1):
                bg = self.pixels[x, y]
                blended = (
                    int(alpha * colour[0] + (1 - alpha) * bg[0]),
                    int(alpha * colour[1] + (1 - alpha) * bg[1]),
                    int(alpha * colour[2] + (1 - alpha) * bg[2]),
                    255
                )
                self.pixels[x, y] = blended

    def draw_pixel(self, xy, colour):
        x, y = xy
        if 0 <= x < self.width and 0 <= y < self.height:
            self.pixels[x, y] = colour

    def annotate(self, pixel_xy, text, text_scale=1.0, line_thickness=1,
                 text_colour=None, line_colour=None, auto_contrast=False, background_colour=None):
        x, y = pixel_xy
        if not (0 <= x < self.width and 0 <= y < self.height):
            return
        bg_color = self.pixels[x, y]
        default_color = (255, 255, 255, 255)
        if auto_contrast:
            if bg_color[0] == bg_color[1] == bg_color[2]:
                contrast_color = (255, 0, 0, 255) if bg_color[0] < 128 else (0, 0, 255, 255)
            else:
                contrast_color = (255 - bg_color[0], 255 - bg_color[1], 255 - bg_color[2], 255)
            if text_colour is None:
                text_colour = contrast_color
            if line_colour is None:
                line_colour = contrast_color
        else:
            if text_colour is None:
                text_colour = default_color
            if line_colour is None:
                line_colour = default_color

        try:
            font = ImageFont.truetype("consola.ttf", int(12 * text_scale))
        except IOError:
            font = ImageFont.load_default()
            if hasattr(font, "size"):
                font = ImageFont.load_default().font_variant(size=int(12 * text_scale))
        text_bbox = self.draw.textbbox((0, 0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        offset = 20
        if x < self.width / 2:
            text_x = x + offset
        else:
            text_x = x - offset - text_width
        if y < self.height / 2:
            text_y = y + offset
        else:
            text_y = y - offset - text_height

        if background_colour is not None:
            padding = 1
            top_left = (text_x - padding, text_y - padding)
            bg_width = text_width + 2 * padding
            bg_height = text_height + 2 * padding
            self.draw_rectangle(top_left, bg_width, bg_height, background_colour)

        self.draw.text((text_x, text_y), text, fill=text_colour, font=font)
        text_box = [
            (text_x, text_y),
            (text_x + text_width, text_y),
            (text_x + text_width, text_y + text_height),
            (text_x, text_y + text_height)
        ]
        min_dist = float('inf')
        closest_point = None
        for corner in text_box:
            dist = math.sqrt((corner[0] - x) ** 2 + (corner[1] - y) ** 2)
            if dist < min_dist:
                min_dist = dist
                closest_point = corner
        angle = math.atan2(closest_point[1] - y, closest_point[0] - x)
        start_x = x + math.cos(angle)
        start_y = y + math.sin(angle)
        self.draw.line([(start_x, start_y), closest_point], fill=line_colour, width=line_thickness)