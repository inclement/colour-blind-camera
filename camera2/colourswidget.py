from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.properties import (StringProperty, BooleanProperty, NumericProperty)
from kivy.clock import Clock
from kivy.graphics import RenderContext

import shaders

class ColourShaderWidget(FloatLayout):
    fs = StringProperty(None)

    transformation = StringProperty('none')

    daltonize = BooleanProperty(False)

    colorimetric_modification = BooleanProperty(False)

    linearize = BooleanProperty(False)

    fraction = NumericProperty(1.0)

    def __init__(self, *args, **kwargs):
        self.canvas = RenderContext(use_parent_projection=True,
                                    use_parent_modelview=True)

        Clock.schedule_once(self.post_init, 0)
        super().__init__(*args, **kwargs)

    def post_init(self, *args):
        self.fs = shaders.shader_colour_blindness

    def on_fs(self, instance, value):
        self.canvas.shader.fs = self.fs

    def on_daltonize(self, instance, value):
        self.canvas['daltonize'] = 1 if self.daltonize else 0

    def on_linearize(self, instance, value):
        self.canvas['linearize'] = 1 if self.linearize else 0

    def on_transformation(self, instance, value):
        self.fs = shaders.shader_colour_blindness
        self.canvas['transformation'] = {
            'none': 0,
            'protanopia': 1,
            'deuteranopia': 2,
            'tritanopia': 3,
            'monochromacy': 4}[value]

    def on_colorimetric_modification(self, instance, value):
        self.canvas['colorimetric_modification'] = 1 if self.colorimetric_modification else 0

    def on_fraction(self, instance, value):
        self.canvas['transform_cutoff'] = self.width * 0.99999

    def on_size(self, instance, value):
        self.on_fraction(self, self.fraction)
