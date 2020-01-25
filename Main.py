# watch: https://www.youtube.com/watch?v=psIQSLmy25A
import argparse
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.graphics import Rectangle, Line, Color, BorderImage
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.core.text import Label as CoreLabel
from GameState import *
from definitions import *


class GameWidget(Widget):
    game_state: GameState
    state_handlers: Dict[str, StateProtocol]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.state_handlers = {STATE_PLAYING: PlayingState()
            , STATE_FALLING: FallingState()
            , STATE_GAME_OVER: GameOverState()
                               }

        # set framewor dependent drawing functions
        self.state_handlers[STATE_GAME_OVER].set_draw(self.draw_game_over)
        self.state_handlers[STATE_PLAYING].set_draw(self.draw_game)
        self.state_handlers[STATE_FALLING].set_draw(self.draw_game)

        self.game_state = GameState(state_handlers=self.state_handlers
                                    , current_handler=self.state_handlers[STATE_PLAYING]
                                    #, current_handler=self.state_handlers[STATE_GAME_OVER]
                                    , occupied_positions={}
                                    , running=True
                                    , current_shape=new_shape()
                                    , next_shape=new_shape()
                                    , fall_time=0
                                    , fall_speed=INITIAL_FALL_SPEED
                                    )
        self.game_state = self.game_state.current_handler.enter(self.game_state)
        self.keyboard = Window.request_keyboard(self.on_keyboard_closed, self)
        self.keyboard.bind(on_key_down=self.on_key_down)
        self.keyboard.bind(on_key_up=self.on_key_up)
        self.translation_tab = {32:EVENT_FALL, 276:EVENT_LEFT, 275:EVENT_RIGHT, 273:EVENT_ROT_LEFT,274:EVENT_ROT_RIGHT}
        self.keys_pressed = set()
        Window.clearcolor = list(map(lambda c:c/255, BACKGROUND_COLOR))+[1]
        if Window.size[0]*0.5/GRID_WIDTH > Window.size[1]*0.7/GRID_HEIGHT:
            self.block_size = Window.size[1] * 0.7 / GRID_HEIGHT
        else:
            self.block_size = Window.size[0] * 0.5 / GRID_WIDTH
        self.grid_size = (self.block_size*GRID_WIDTH, self.block_size*GRID_HEIGHT)
        self.grid_pos = (Window.size[0]*0.5 - self.grid_size[0]*0.5,Window.size[1]*0.5 - self.grid_size[1]*0.5)
        Clock.schedule_interval(self.game_loop, 1/30)

    def game_loop(self, dt):
        self.game_state.fall_time += (dt*1000)
        self.game_state = self.game_state.current_handler.update(self.game_state)
        self.game_state.current_handler.draw(self.game_state)

    def on_key_down(self, keyboard, keycode, text, modifier):
        key = keycode[0]
        print(key)
        self.game_state = self.game_state.current_handler.handle_event(self.game_state,
                                                                       self.translate_key_to_event(key))
        self.keys_pressed.add(key)

    def on_key_up(self, keyboard, keycode):
        key = keycode[0]
        if key in self.keys_pressed:
            self.keys_pressed.remove(key)

    def on_keyboard_closed(self):
        self.keyboard.unbind(on_key_down=self.on_key_down)
        self.keyboard.unbind(on_key_up=self.on_key_up)

    def translate_key_to_event(self, key: int) -> EventType:
        try:
            return self.translation_tab[key]
        except KeyError:
            return EVENT_NONE

    def draw_title(self):
        with self.canvas:
            # draw TITLE label
            label = CoreLabel(text=TITLE, font_size=60)
            label.refresh()
            text = label.texture
            pos = ((Window.size[0] - text.size[0]) / 2, (Window.size[1] * 1.85 - text.size[1]) * 0.5)
            Color(*map(lambda c: c / 255, LINE_COLOR1))
            Rectangle(size=text.size, pos=pos, texture=text)

    def draw_score(self, score: int):
        with self.canvas:
            # draw Score label
            label = CoreLabel(text=SCORE_LABEL + str(score), font_size=40)
            label.refresh()
            text = label.texture
            pos = (Window.size[0] * 0.95 - text.size[0], (Window.size[1] * 1.85 - text.size[1]) * 0.5)
            Color(*map(lambda c: c / 255, WHITE))
            Rectangle(size=text.size, pos=pos, texture=text)

    def draw_next_shape(self, shape):
        with self.canvas:
            Color(*map(lambda c: c/255, shape.color))
            coords = []
            templ = shapes[shape.shapeIdx][0]
            for (y, row) in enumerate(templ):
                for (x, cell) in enumerate(row):
                    if cell == 'X':
                        coords.append((NEXT_SHAPE_START_X + x + SHAPE_OFFSET_X, NEXT_SHAPE_START_Y + y + SHAPE_OFFSET_Y))
            for (x, y) in coords:
                xcoord = self.grid_pos[0] + x * self.block_size
                ycoord = self.grid_pos[1] + (GRID_HEIGHT-y-1) * self.block_size
                Rectangle(pos=(xcoord,ycoord), size=(self.block_size-1, self.block_size-1))

    def draw_grid(self):
        with self.canvas:
            # draw red frame
            Color(*map(lambda c: c / 255, WHITE))
            Rectangle(size=self.grid_size
                      , pos=self.grid_pos)

            Color(*map(lambda c:c/255, LINE_COLOR))
            for y in range(GRID_HEIGHT):
                # horizontal lines
                ylevel = self.grid_pos[1] + y * self.block_size
                Line(width=1,
                     points=(self.grid_pos[0], ylevel, self.grid_pos[0]+self.grid_size[0], ylevel))
            for x in range(GRID_WIDTH):
                # vertical lines
                xlevel = self.grid_pos[0] + x * self.block_size
                Line(width=1,
                     points=(xlevel, self.grid_pos[1], xlevel, self.grid_pos[1] + GRID_HEIGHT * self.block_size))

    def draw_shapes(self, occupied_positions, current_shape):
        with self.canvas:
            for ((x, y), shape) in occupied_positions.items():
                Color(*map(lambda c: c / 255, shape.color))
                xcoord = self.grid_pos[0] + x * self.block_size
                ycoord = self.grid_pos[1] + (GRID_HEIGHT-y-1) * self.block_size
                Rectangle(pos=(xcoord,ycoord), size=(self.block_size-1, self.block_size-1))

            Color(*map(lambda c: c/255, current_shape.color))
            current_shape_positions = shape_to_grid(current_shape)
            for (x, y) in current_shape_positions:
                xcoord = self.grid_pos[0] + x * self.block_size
                ycoord = self.grid_pos[1] + (GRID_HEIGHT-y-1) * self.block_size
                Rectangle(pos=(xcoord, ycoord), size=(self.block_size-1, self.block_size-1))

    def draw_game(self, state: GameState):
        self.canvas.clear()

        self.draw_title()
        self.draw_score(state.score)

        self.draw_next_shape(state.next_shape)
        self.draw_grid()
        self.draw_shapes(state.occupied_positions, state.current_shape)

        self.canvas.ask_update()

    def draw_game_over(self, state: GameState):
        self.canvas.clear()
        self.draw_title()
        self.draw_score(state.score)
        with self.canvas:
            # draw restart question label
            label = CoreLabel(text=RESTART_LABEL, font_size=60)
            label.refresh()
            text = label.texture
            pos = ((Window.size[0] - text.size[0])*0.5, (Window.size[1] - text.size[1]) * 0.5)
            Color(*map(lambda c: c / 255, GREEN))
            Rectangle(size=text.size, pos=pos, texture=text)

        self.canvas.ask_update()



class GameApp(App):
    def build(self):
        return GameWidget()


if __name__ == '__main__':
    GameApp().run()
