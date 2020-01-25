from typing import *

from copy import copy
from dataclasses import dataclass

from logic import *
from itertools import *
from more_itertools import *


@dataclass()
class GameState(object):
    state_handlers: Dict[str, Any] #StateProtocol] -- Foreward Declaration needed
    current_handler: Any #StateProtocol
    occupied_positions: Dict[Tuple[int, int], Shape]
    running: bool
    current_shape: Shape
    next_shape: Shape
    fall_time: int
    fall_speed: float
    score: int = 0


def glue_current_shape_and_clear_rows_while_counting_score(state: GameState) -> GameState:
    # glue current shape
    shape_coord = shape_to_grid(state.current_shape)
    for coord in shape_coord:
        state.occupied_positions[copy(coord)] = state.current_shape

    # clear fully occupied rowes

    # identify rows that can be deleted
    k1 = sorted(state.occupied_positions.keys(), key=lambda k: k[1])
    k2 = groupby(k1, key=lambda k: k[1])
    k3 = map(lambda k: (k[0], sum(map(lambda l: l[0], k[1]))), k2)
    k4 = filter(lambda k: k[1] == GAUSS_GRID_SUM, k3)
    k5 = set(map(lambda k: k[0], k4))
    # print(k5)

    # count score

    # delete all elemens of the rows
    state.occupied_positions = dict(((x, y), v) for ((x, y), v) in state.occupied_positions.items()
                                    if y not in k5)

    # slide blocks downwards
    k6 = sorted(k5, reverse=False)
    for y in k6:
        for y1 in range(y - 1, -1, -1):
            for x in range(GRID_WIDTH):
                if is_within_grid(x, y1) and (x, y1) in state.occupied_positions:
                    state.occupied_positions[(x, y1 + 1)] = state.occupied_positions[(x, y1)]
                    del state.occupied_positions[(x, y1)]

    # count score
    state.score += len(k5)

    return state


def move_shape(state: GameState) -> Tuple[bool, GameState]:
    if state.fall_time / 1000 > state.fall_speed:
        state.fall_time = 0
        state.current_shape.y += 1
        if not space_valid_for_shape(state.current_shape, state.occupied_positions) and not is_spawn_pos(
                (state.current_shape.x, state.current_shape.y)):
            state.current_shape.y -= 1
            return False, state
    return True, state


#class StateProtocol(Protocol):
class StateProtocol(object):

    draw_internal: Callable[[GameState], None]

#    def __init__(self, draw_fn: Callable[[GameState], None]):
#        self.draw_internal = draw_fn

    def set_draw(self, draw_fn: Callable[[GameState], None]):
        self.draw_internal = draw_fn

    def enter(self, state: GameState) -> GameState:
        state.current_handler = self
        return state

    def leave(self, state: GameState) -> GameState:
        raise NotImplementedError

    def handle_event(self, state: GameState, event: EventType) -> GameState:
        raise NotImplementedError

    def update(self, state: GameState) -> GameState:
        raise NotImplementedError

    def draw(self, state: GameState) -> None:
        if not self.draw_internal:
            raise NotImplementedError
        else:
            self.draw_internal(state)


class GameOverState(StateProtocol):
    def leave(self, state: GameState) -> GameState:
        state.fall_speed = INITIAL_FALL_SPEED
        state.occupied_positions = {}
        state.score = 0
        return state

    def enter(self, state: GameState) -> GameState:
        state = super().enter(state)
        return state

    def handle_event(self, state: GameState, event: EventType) -> GameState:
        """
        :param state: will be mutated
        :param event:
        :return: Tuple new state handler, mutated state
        """
        # quit
        if event == EVENT_QUIT:
            state.running = False
        else:
            new_state_handler = state.state_handlers[STATE_PLAYING]
            return new_state_handler.enter(self.leave(state))

        return state

    def update(self, state: GameState) -> Tuple[StateProtocol, GameState]:
        """
        :param state: will be mutates
        :return: Tuple new state handler, mutated state
        """
        return state


class PlayingState(StateProtocol):
    def leave(self, state: GameState) -> GameState:
        return state

    def enter(self, state: GameState) -> GameState:
        state = super().enter(state)
        state.current_shape = state.next_shape
        state.next_shape = new_shape()
        state.fall_speed = INITIAL_FALL_SPEED
        return state

    def handle_event(self, state: GameState, event: EventType) -> GameState:
        """
        :param state: will be mutated
        :param event:
        :return: Tuple new state handler, mutated state
        """
        # mutating state
        if event == EVENT_QUIT:
            state.running = False
        else:
            if event == EVENT_FALL:
                new_state_handler = state.state_handlers[STATE_FALLING]
                return new_state_handler.enter(self.leave(state))
            else:
                # stearing the shape
                state.current_shape_copy = copy(state.current_shape)
                if event == EVENT_LEFT:
                    state.current_shape.x -= 1
                if event == EVENT_RIGHT:
                    state.current_shape.x += 1
                if event == EVENT_ROT_LEFT:
                    state.current_shape.rotation -= 1
                if event == EVENT_ROT_RIGHT:
                    state.current_shape.rotation += 1
                if not (space_valid_for_shape(state.current_shape, state.occupied_positions)):
                    state.current_shape = state.current_shape_copy

        return state

    def update(self, state: GameState) -> GameState:
        """
        :param state: will be mutates
        :return: Tuple new state handler, mutated state
        """

        shape_move_successful, state = move_shape(state)

        if not shape_move_successful:
            state = glue_current_shape_and_clear_rows_while_counting_score(state)
            if check_lost(state.occupied_positions):
                new_state_handler = state.state_handlers[STATE_GAME_OVER]
                return new_state_handler.enter(self.leave(state))
            else:
                state = self.enter(self.leave(state))

        return state


class FallingState(StateProtocol):
    def enter(self, state: GameState) -> GameState:
        state = super().enter(state)
        return state

    def leave(self, state: GameState) -> GameState:
        return state

    def handle_event(self, state: GameState, event: EventType) -> GameState:
        """
        :param state: will be mutated
        :param event:
        :return: Tuple new state handler, mutated state
        """
        # quit
        if event == EVENT_QUIT:
            state.running = False

        return state

    def update(self, state: GameState) -> GameState:
        """
        :param state: will be mutates
        :return: Tuple new state handler, mutated state
        """
        state.fall_speed *= 0.9
        shape_move_successful, state = move_shape(state)

        if not shape_move_successful:
            state = glue_current_shape_and_clear_rows_while_counting_score(state)
            if check_lost(state.occupied_positions):
                new_state_handler = state.state_handlers[STATE_GAME_OVER]
                return new_state_handler.enter(self.leave(state))
            else:
                new_state_handler = state.state_handlers[STATE_PLAYING]
                state = new_state_handler.enter(self.leave(state))
                return state

        return state
