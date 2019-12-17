from kivy.uix.behaviors import ButtonBehavior, ToggleButtonBehavior
from kivy.uix.button import Button
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.label import Label
from kivy.properties import (ListProperty, NumericProperty, BooleanProperty)
from kivy.metrics import dp

class ColouredButton(ButtonBehavior, Label):
    background_normal = ListProperty([1, 1, 1, 1])
    background_down = ListProperty([0.5, 0.5, 0.5, 1])
    padding = NumericProperty(dp(2))
    radius = NumericProperty(dp(5))

class ColouredToggleButton(ToggleButtonBehavior, Label):
    background_normal = ListProperty([1, 1, 1, 1])
    background_down = ListProperty([0.5, 0.5, 0.5, 1])
    padding = NumericProperty(dp(2))
    radius = NumericProperty(dp(5))

class ColouredButtonContainer(ButtonBehavior, AnchorLayout):
    background_normal = ListProperty([1, 1, 1, 1])
    background_down = ListProperty([0.5, 0.5, 0.5, 1])
    coloured_button_padding = NumericProperty(dp(2))
    radius = NumericProperty(dp(5))

class ColouredToggleButtonContainer(ToggleButtonBehavior, AnchorLayout):
    background_normal = ListProperty([1, 1, 1, 1])
    background_down = ListProperty([0.5, 0.5, 0.5, 1])
    coloured_button_padding = NumericProperty(dp(2))
    radius = NumericProperty(dp(5))

class ButtonCheckbox(ButtonBehavior, Label):
    active = BooleanProperty(True)
    box_size = NumericProperty()
    draw_colour = ListProperty((0.2, 0.2, 0.2, 1))
    text_colour = ListProperty((0.0, 0.0, 0.0, 1))
    handle_touch = BooleanProperty(True)

    def on_touch_down(self, touch):
        if not self.handle_touch:
            return False
        return super(ButtonCheckbox, self).on_touch_down(touch)
