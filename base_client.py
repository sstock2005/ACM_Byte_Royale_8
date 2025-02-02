import random

from game.client.user_client import UserClient
from game.commander_clash.character.character import Character
from game.common.enums import *
from game.common.map.game_board import GameBoard
from game.common.team_manager import TeamManager
from game.utils.vector import Vector

class State(Enum):
    HEALTHY = auto()
    UNHEALTHY = auto()


class Client(UserClient):
    # Variables and info you want to save between turns go here
    def __init__(self):
        super().__init__()

    def team_data(self) -> tuple[str, tuple[SelectGeneric, SelectLeader, SelectGeneric]]:
        """
        Returns your team name (to be shown on visualizer) and a tuple of enums representing the characters you
        want for your team. The tuple of the team must be ordered as (Generic, Leader, Generic). If an enum is not
        placed in the correct order (e.g., (Generic, Leader, Leader)), whichever selection is incorrect will be
        swapped with a default value of Generic Attacker.
        """
        return 'KAOTIC', (SelectGeneric.GEN_HEALER, SelectLeader.CALMUS, SelectGeneric.GEN_ATTACKER)

    def first_turn_init(self, team_manager: TeamManager):
        """
        This is where you can put setup for things that should happen at the beginning of the first turn. This can be
        edited as needed.
        """
        self.country = team_manager.country_type
        self.my_team = team_manager.team
        self.current_state = State.HEALTHY

    def get_health_percentage(self, character: Character):
        """
        Returns a float representing the health of the given character.
        :param character: The character to get the health percentage for.
        """
        return float(character.current_health / character.max_health)

    # This is where your AI will decide what to do
    def take_turn(self, turn: int, actions: list[ActionType], world: GameBoard, team_manager: TeamManager):
        """
        This is where your AI will decide what to do.
        :param turn:         The current turn of the game.
        :param actions:      This is the actions object that you will add effort allocations or decrees to.
        :param world:        Generic world information
        :param team_manager: A class that wraps the list of Characters to control
        """
        if turn == 1:
            self.first_turn_init(team_manager)

        # get your active character for the turn; may be None
        active_character: Character = self.get_my_active_char(team_manager, world)

        # if there is no active character for my team on this current turn, return an empty list
        if active_character is None:
            return []


        if self.country == CountryType.URODA:
            enemy_x = 1
        else:
            enemy_x = 0

        active_enemy: Character = world.get_character_from(Vector(1, active_character.position.y))
        
        # determine if the active character is healthy
        current_state: State = State.HEALTHY if self.get_health_percentage(
            active_character) >= 0.50 else State.UNHEALTHY
        
        attacker_move = False
        healer_move = False

        actions: list[ActionType]

        ### GAME LOGIC ###

        ## GEN HEALER LOGIC ##

        if active_character.rank_type == RankType.GENERIC and active_character.class_type == ClassType.HEALER:
            if active_enemy:
                healer_move = True
            else:
                healer_move = False
            
            if healer_move:
                for position in world.get_in_bound_coords():
                    is_character = world.get_character_from(position)
                    if not is_character and position.x == enemy_x:
                        position_offset = active_character.position.y - position.y

                        if position_offset > 0:
                            actions = [ActionType.SWAP_UP]
                            break
                        elif position_offset < 0:
                            actions = [ActionType.SWAP_DOWN]
                            break
                        
            if active_character.current_health < 200:
                actions.append(ActionType.USE_S1)
            elif active_character.special_points >= 3:
                actions.append(ActionType.USE_S2)
            else:
                actions.append(ActionType.USE_NM)
            
        ## CALMUS LOGIC ##

        if active_character.rank_type == RankType.LEADER:
            if active_character.special_points >= 5:
                actions = [ActionType.USE_S2]
            else:
                actions = [ActionType.USE_NM]
                
        ## GEN ATTACKER LOGIC ##

        if active_character.rank_type == RankType.GENERIC and active_character.class_type == ClassType.ATTACKER:
            if active_enemy:
                if active_enemy.class_type != ClassType.HEALER:
                    attacker_move = True
            else:
                attacker_move = True

            if attacker_move:
                 for position in world.get_in_bound_coords():
                    is_character = world.get_character_from(position)

                    if position.x == enemy_x and is_character:
                        if is_character.class_type == ClassType.HEALER:
                            position_offset = active_character.position.y - position.y

                            if position_offset > 0:
                                actions = [ActionType.SWAP_UP]
                                break
                            elif position_offset < 0:
                                actions = [ActionType.SWAP_DOWN]    
                                break

            if active_character.special_points >= 1:
                actions.append(ActionType.USE_S1)
            else:
                actions.append(ActionType.USE_NM)

        return actions

    def get_my_active_char(self, team_manager: TeamManager, world: GameBoard) -> Character | None:
        """
        Returns your active character based on which characters have already acted. If None is returned, that means
        none of your characters can act again until the turn order refreshes. This also means your team has fewer
        characters than the opponent.
        """

        active_character = team_manager.get_active_character(world.ordered_teams, world.active_pair_index)

        return active_character
