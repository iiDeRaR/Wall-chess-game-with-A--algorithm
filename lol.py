
import pygame  #For game rendering and input handling
import heapq  #For priority queue in A*
import sys
import time  #For delaying ai turns in ai vs ai mode

#Game configration
BOARD_COLS, BOARD_ROWS = 9, 9
GOAL_ROWS = 2  #Additional rows for goal areas
TOTAL_ROWS = BOARD_ROWS + GOAL_ROWS  #Total rows including goals
TILE_SIZE = 500 // BOARD_COLS
SCREEN_WIDTH = BOARD_COLS * TILE_SIZE
SCREEN_HEIGHT = TOTAL_ROWS * TILE_SIZE
FPS = 10  #Frames per second for game loop
MAX_WALLS_PER_PLAYER = 10

#Colors for gui
WHITE = (255, 255, 255)
BLACK= (0, 0, 0)
BLUE = (0, 0, 255)  #Player1 color
RED = (255, 0, 0)  #ai/Player2 color
GREEN = (0, 255, 0)
GRAY = (200, 200, 200)
BUTTON_COLOR = (100, 100, 255)
BUTTON_HOVER_COLOR = (150, 150, 255)
SCORE_COLOR = (50, 50, 150)
MODE_BUTTON_COLOR = (100, 255, 100)
TITLE_COLOR = (50, 50, 150)

#pygame intialize
pygame.init()  #Initialize all pygame modules
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))  #Create game window
pygame.display.set_caption("Wall Chess")  #Game title
clock = pygame.time.Clock()  #For controlling game speed

#Font setup for ui elements
font = pygame.font.SysFont(None, 24)
large_font = pygame.font.SysFont(None, 36)
title_font = pygame.font.SysFont(None, 48)


#Class for path finding
class Node:

    def __init__(self, row, col, parent=None):
        self.row = row  #Row position on board
        self.col = col  #Column position on board
        self.parent = parent  #Previous node in path
        self.g = 0  #Cost from start to current node
        self.h = 0  #Heuristic cost to goal
        self.f = 0  #Total cost f=(g+h)

    def __lt__(self, other):
        #Comparison method for A* that chooses the least f
        return self.f < other.f


#Calculate h for f=(g+h)
def heuristic(node, goal_pos):

    return abs(node.row - goal_pos[0]) + abs(node.col - goal_pos[1])

"""
    A* pathfinding algorithm to find shortest path from start to goal
    while avoiding walls

    Returns:
        list: Path as [(row1,col1), (row2,col2), ..., (rown,clon)] or empty list if no path found or reached goal
    """
def a_star(start_node, goal_pos, walls):

    open_set = [(0, start_node)]  #Priority queue of nodes to explore
    visited = set()  #Set of visited nodes

    while open_set:
        #Get node with lowest f-score from priority queue
        _, current = heapq.heappop(open_set)

        #Check if goal reached
        if (current.row, current.col) == goal_pos:
            #Create path by following parent pointers
            path = []
            while current.parent:
                path.append((current.row, current.col))
                current = current.parent
            return list(reversed(path))  #Return path from start to goal

        visited.add((current.row, current.col))  #Mark current node as visited

        #Check all 4 possible movement directions to neighbor node
        for drow, dcol in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            nr, nc = current.row + drow, current.col + dcol  # Neighbor position

            #Check if neighbor is the goal
            if (nr, nc) == goal_pos:
                neighbor = Node(nr, nc, current)
            #Skip path if out of bounds (excluding goal rows)
            elif not (1 <= nr < TOTAL_ROWS - 1 and 0 <= nc < BOARD_COLS):
                continue
            #Skip path if wall exists at neighbor node
            elif (nr, nc) in walls:
                continue
            #Valid empty position
            else:
                neighbor = Node(nr, nc, current)

            #Calculate path costs
            neighbor.g = current.g + 1  #Movement cost (1 per step)
            neighbor.h = heuristic(neighbor, goal_pos)  #Estimated cost to goal
            neighbor.f = neighbor.g + neighbor.h  #Total estimated cost

            #Add to open set if not already visited
            if (nr, nc) not in visited:
                heapq.heappush(open_set, (neighbor.f, neighbor))

    return []  #Return empty list if no path found or goal reached


#Render functions for gui
def draw_grid():

    for x in range(0, SCREEN_WIDTH + 1, TILE_SIZE):
        pygame.draw.line(screen, BLACK, (x, 0), (x, SCREEN_HEIGHT))
    for y in range(0, SCREEN_HEIGHT + 1, TILE_SIZE):
        pygame.draw.line(screen, BLACK, (0, y), (SCREEN_WIDTH, y))


def draw_tile(row, col, color):
    pygame.draw.rect(screen, color,
                     (col * TILE_SIZE, row * TILE_SIZE, TILE_SIZE, TILE_SIZE))

#Function for buttons in gui
def draw_button(x, y, width, height, text, color, hover_color, hover=False):
    btn_color = hover_color if hover else color
    pygame.draw.rect(screen, btn_color, (x, y, width, height))
    pygame.draw.rect(screen, BLACK, (x, y, width, height), 2)

    #Render button text
    text_surf = font.render(text, True, BLACK)
    text_rect = text_surf.get_rect(center=(x + width / 2, y + height / 2))
    screen.blit(text_surf, text_rect)

#Function for score counter
def draw_score_counter(player_wins, ai_wins, games_played):
    score_text = f"Player: {player_wins} | AI: {ai_wins} | Games: {games_played}"
    score_surf = font.render(score_text, True, SCORE_COLOR)
    score_rect = score_surf.get_rect(topright=(SCREEN_WIDTH - 10, 10))
    screen.blit(score_surf, score_rect)


#Function to start the game with default settings
def reset_game():
    return {
        'player_pos': [1, BOARD_COLS // 2],  #Player starting position
        'ai_pos': [TOTAL_ROWS - 2, BOARD_COLS // 2],  #AI starting position
        'player_goal': (TOTAL_ROWS - 1, BOARD_COLS // 2),  #Player goal position
        'ai_goal': (0, BOARD_COLS // 2),  #AI goal position
        'walls': set(),  #Set of wall positions
        'player_walls_used': 0,  #Walls placed by player
        'ai_walls_used': 0,  #Walls placed by AI
        'turn_counter': 0,  #Track turns for AI modes
        'game_over': False,  #Game completion flag
        'result_message': "",  #Win/lose message
        'player_moved': False  #Player turn completion
    }

"""
    Process the ai's turn places walls and moves toward goal

    Arguments:
        game_state:Current game state
        is_player_ai:Whether this is the player ai (in ai vs ai mode)

    Returns:
        Updated game state (HUD)
"""
def handle_ai_turn(game_state, is_player_ai=False):
    game_state['turn_counter'] += 1  #Increment turn counter

    #Determine which ai is moving based on mode
    if is_player_ai:
        current_ai_pos = game_state['player_pos']
        current_ai_goal = game_state['player_goal']
        walls_used = game_state['player_walls_used']
    else:
        current_ai_pos = game_state['ai_pos']
        current_ai_goal = game_state['ai_goal']
        walls_used = game_state['ai_walls_used']

    #Ai wall placement logic (if walls remain)
    if walls_used < MAX_WALLS_PER_PLAYER:
        #Get opponent's position and goal
        opponent_pos = game_state['ai_pos'] if is_player_ai else game_state['player_pos']
        opponent_goal = game_state['ai_goal'] if is_player_ai else game_state['player_goal']

        #Find opponent's current path
        opponent_path = a_star(Node(*opponent_pos), opponent_goal, game_state['walls'])

        if opponent_path:
            #Try to block the first step of opponent's path
            block_pos = opponent_path[0]
            walls_candidate = game_state['walls'].copy()
            walls_candidate.add(block_pos)

            #Wall counter
            if (a_star(Node(*game_state['player_pos']), game_state['player_goal'], walls_candidate)
                    and a_star(Node(*game_state['ai_pos']), game_state['ai_goal'], walls_candidate)):
                game_state['walls'] = walls_candidate
                if is_player_ai:
                    game_state['player_walls_used'] += 1
                else:
                    game_state['ai_walls_used'] += 1
                print(f"{'Player AI' if is_player_ai else 'AI'} placed wall at {block_pos}")

    #Ai movement towards goal (HUD)
    ai_path = a_star(Node(*current_ai_pos), current_ai_goal, game_state['walls'])
    if ai_path:
        if is_player_ai:
            game_state['player_pos'][0], game_state['player_pos'][1] = ai_path[0]
        else:
            game_state['ai_pos'][0], game_state['ai_pos'][1] = ai_path[0]
        print(f"{'Player AI' if is_player_ai else 'AI'} moved to {ai_path[0]}")

    #Check if won conditions
    if tuple(game_state['player_pos']) == game_state['player_goal']:
        game_state[
            'result_message'] = "Player AI reached the goal! Player AI wins!" if is_player_ai else "You reached the AI's goal! You win!"
        game_state['game_over'] = True
    elif tuple(game_state['ai_pos']) == game_state['ai_goal']:
        game_state['result_message'] = "AI reached the goal! AI wins!"
        game_state['game_over'] = True

    return game_state


#Start menu gui
def show_start_screen():

    while True:
        screen.fill(WHITE)

        #Draw game title
        title_surf = title_font.render("Welcome to Wall Chess!", True, TITLE_COLOR)
        title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 4))
        screen.blit(title_surf, title_rect)

        #Draw instructions
        instr_surf = font.render("Select game mode:", True, BLACK)
        instr_rect = instr_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
        screen.blit(instr_surf, instr_rect)


        button_width, button_height = 200, 50
        button_x = (SCREEN_WIDTH - button_width) // 2  # Center buttons horizontally


        pvp_button_y = SCREEN_HEIGHT // 2

        aiva_button_y = pvp_button_y + button_height + 20


        pvp_button_rect = pygame.Rect(button_x, pvp_button_y, button_width, button_height)
        aiva_button_rect = pygame.Rect(button_x, aiva_button_y, button_width, button_height)

        #Track mouse state
        mouse_pos = pygame.mouse.get_pos()
        mouse_clicked = False

        #Event handling loop for mouse
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_clicked = True


        pvp_hover = pvp_button_rect.collidepoint(mouse_pos)
        aiva_hover = aiva_button_rect.collidepoint(mouse_pos)


        draw_button(button_x, pvp_button_y, button_width, button_height,
                    "Player vs AI", BUTTON_COLOR, BUTTON_HOVER_COLOR, pvp_hover)
        draw_button(button_x, aiva_button_y, button_width, button_height,
                    "AI vs AI", BUTTON_COLOR, BUTTON_HOVER_COLOR, aiva_hover)

        #Handle mouse clicks
        if mouse_clicked:
            if pvp_hover:
                return 0  #Player vs ai mode
            elif aiva_hover:
                return 1  #ai vs ai mode

        pygame.display.flip()  #Update display
        clock.tick(FPS)  #Maintain frame rate


#Main game function
def main():

    #Show start screen and get selected game mode
    game_mode = show_start_screen()  #0=Player vs ai, 1=ai vs ai
    game_state = reset_game()  #Initialize default game state

    #Initialize score tracking
    scores = {
        'player_wins': 0,  #Player win count
        'ai_wins': 0,  #Ai win count
        'games_played': 0  #Total games played
    }

    #Replay button setup
    button_width, button_height = 200, 50
    button_x = (SCREEN_WIDTH - button_width) // 2
    button_y = (SCREEN_HEIGHT - button_height) // 2
    replay_button_rect = pygame.Rect(button_x, button_y - 70, button_width, button_height)

    #Mode switch button setup
    mode_button_width, mode_button_height = 250, 40
    mode_button_x = (SCREEN_WIDTH - mode_button_width) // 2
    mode_button_y = button_y
    mode_button_rect = pygame.Rect(mode_button_x, mode_button_y, mode_button_width, mode_button_height)

    #Quit to home button setup
    home_button_width, home_button_height = 200, 50
    home_button_x = (SCREEN_WIDTH - home_button_width) // 2
    home_button_y = button_y + 70
    home_button_rect = pygame.Rect(home_button_x, home_button_y, home_button_width, home_button_height)

    game_running = True  #Main game loop statement
    ai_turn_delay = 0.5  #Delay between ai moves in ai vs ai mode

    #Game loop
    while game_running:
        clock.tick(FPS)  #Control game speed

        #Track mouse state
        mouse_pos = pygame.mouse.get_pos()
        mouse_clicked = False

        #Event handling for quiting game
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game_running = False  #Exit game loop

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_clicked = True  #Check if left mouse button clicked and place a wall

            #Handle player movement (only in Player vs AI mode)
            if (not game_state['game_over'] and game_mode == 0
                    and not game_state['player_moved'] and event.type == pygame.KEYDOWN):
                row, col = game_state['player_pos']

                #Movement handling (WASD keys)
                if event.key == pygame.K_w:  #W for Up
                    if ((row - 1, col) == game_state['player_goal'] or
                            (row > 1 and (row - 1, col) not in game_state['walls'])):
                        game_state['player_pos'][0] -= 1
                        game_state['player_moved'] = True
                elif event.key == pygame.K_s:  #S for Down
                    if ((row + 1, col) == game_state['player_goal'] or
                            (row < TOTAL_ROWS - 2 and (row + 1, col) not in game_state['walls'])):
                        game_state['player_pos'][0] += 1
                        game_state['player_moved'] = True
                elif event.key == pygame.K_a:  #A for Left
                    if col > 0 and (row, col - 1) not in game_state['walls']:
                        game_state['player_pos'][1] -= 1
                        game_state['player_moved'] = True
                elif event.key == pygame.K_d:  #D for Right
                    if col < BOARD_COLS - 1 and (row, col + 1) not in game_state['walls']:
                        game_state['player_pos'][1] += 1
                        game_state['player_moved'] = True
                #Display movement in HUD
                if game_state['player_moved']:
                    print(f"Player moved to {game_state['player_pos']}")

        #Clear screen
        screen.fill(WHITE)

        #Game rendering
        if not game_state['game_over']:
            #Draw game board
            draw_grid()

            #Draw all walls
            for wall in game_state['walls']:
                draw_tile(*wall, GRAY)

            #Draw goal areas
            draw_tile(*game_state['player_goal'], GREEN)
            draw_tile(*game_state['ai_goal'], GREEN)

            #Draw player and AI pieces
            draw_tile(game_state['player_pos'][0], game_state['player_pos'][1], BLUE)
            draw_tile(game_state['ai_pos'][0], game_state['ai_pos'][1], RED)

            #Display wall counters
            screen.blit(
                font.render(f"Player walls left: {MAX_WALLS_PER_PLAYER - game_state['player_walls_used']}",
                            True, BLACK),
                (10, 10))
            screen.blit(
                font.render(f"AI walls left: {MAX_WALLS_PER_PLAYER - game_state['ai_walls_used']}",
                            True, BLACK),
                (10, 30))

            #Display score counter
            draw_score_counter(scores['player_wins'], scores['ai_wins'], scores['games_played'])

            #Player wall placement
            if game_mode == 0 and mouse_clicked and not game_state['player_moved']:
                #Convert mouse position to grid coordinates for wall placement
                clicked_row = mouse_pos[1] // TILE_SIZE
                clicked_col = mouse_pos[0] // TILE_SIZE
                clicked_cell = (clicked_row, clicked_col)

                #Validate wall placement position
                if clicked_cell not in [tuple(game_state['player_pos']),
                                        tuple(game_state['ai_pos']),
                                        game_state['player_goal'],
                                        game_state['ai_goal']]:
                    #Check if wall already exists
                    if clicked_cell in game_state['walls']:
                        print("Wall already exists there. No removal allowed!")
                    #Check if player has walls remaining
                    elif game_state['player_walls_used'] >= MAX_WALLS_PER_PLAYER:
                        print("No player walls left.")
                    else:
                        #Test if wall placement would trap either players(no trap rule)
                        walls_candidate = game_state['walls'].copy()
                        walls_candidate.add(clicked_cell)

                        #Handle wall placement
                        if (a_star(Node(*game_state['player_pos']), game_state['player_goal'], walls_candidate)
                                and a_star(Node(*game_state['ai_pos']), game_state['ai_goal'], walls_candidate)):
                            game_state['walls'] = walls_candidate
                            game_state['player_walls_used'] += 1
                            print(f"Player placed wall at {clicked_cell}")
                        else:
                            print("Invalid placement: would trap a player.")

            #Game mode
            #Player vs ai mode
            if game_mode == 0:
                if game_state['player_moved']:
                    game_state = handle_ai_turn(game_state)
                    game_state['player_moved'] = False  #Reset for next match

            #ai vs ai spectator mode
            else:
                time.sleep(ai_turn_delay)  #Slow down AI turns for viewing

                #Alternate between ai 1 and ai 2 turns
                if game_state['turn_counter'] % 2 == 0:  #ai 1's turn
                    game_state = handle_ai_turn(game_state, True)
                else:  #ai 2's turn
                    game_state = handle_ai_turn(game_state, False)

            #Check winning condition and win counter
            if game_state['game_over']:
                if tuple(game_state['player_pos']) == game_state['player_goal']:
                    if game_mode == 1:  #In spectator mode
                        scores['player_wins'] += 1  #Count as AI 1 win
                    else:
                        scores['player_wins'] += 1  # Player win
                    scores['games_played'] += 1
                elif tuple(game_state['ai_pos']) == game_state['ai_goal']:
                    scores['ai_wins'] += 1  # AI win
                    scores['games_played'] += 1

        #Game over screen
        else:
            #Display result message (won/lost

            text_surf = large_font.render(game_state['result_message'], True, BLACK)
            text_rect = text_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 100))
            screen.blit(text_surf, text_rect)

            #Draw replay button
            replay_hover = replay_button_rect.collidepoint(mouse_pos)
            draw_button(button_x, button_y - 70, button_width, button_height,
                        "Play Again", BUTTON_COLOR, BUTTON_HOVER_COLOR, replay_hover)

            #Draw mode switch button
            mode_hover = mode_button_rect.collidepoint(mouse_pos)
            mode_text = "Switch to Player vs AI" if game_mode == 1 else "Switch to AI vs AI"
            draw_button(mode_button_x, mode_button_y, mode_button_width, mode_button_height,
                        mode_text, MODE_BUTTON_COLOR, BUTTON_HOVER_COLOR, mode_hover)

            #Draw quit to home button
            home_hover = home_button_rect.collidepoint(mouse_pos)
            draw_button(home_button_x, home_button_y, home_button_width, home_button_height,
                        "Quit to Home", BUTTON_COLOR, BUTTON_HOVER_COLOR, home_hover)

            #Handle button clicks on game over screen
            if mouse_clicked:
                if replay_hover:
                    game_state = reset_game()  #Restart same mode
                elif mode_hover:
                    game_mode = 1 - game_mode  #Toggle between modes
                    game_state = reset_game()
                elif home_hover:
                    game_mode = show_start_screen()  #Return to start screen
                    game_state = reset_game()
                    scores = {'player_wins': 0, 'ai_wins': 0, 'games_played': 0}

        #Update display
        pygame.display.flip()

    #Clean up pygame and exit
    pygame.quit()
    sys.exit()


#Start game when script is run directly
if __name__ == "__main__":
    main()

