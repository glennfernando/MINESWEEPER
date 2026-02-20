import pygame
import sys
from engine.game import GameEngine
from engine.ai import AIAgent
from ui.renderer import Renderer

def reset_game(level, shape, renderer=None):
    game = GameEngine(level=level, shape=shape)
    ai = AIAgent(game)
    if renderer is not None:
        renderer.reset_timer()
    return game, ai

def main():
    renderer = Renderer(cell_size=32)
    game, ai = reset_game('intermediate', 'square', renderer)
    
    screen = pygame.display.set_mode(renderer.get_window_size(game))
    pygame.display.set_caption("Minesweeper AI")
    
    clock = pygame.time.Clock()
    
    auto_play = False
    show_probs = True
    ai_timer = 0
    AI_DELAY = 100 # ms
    
    while True:
        dt = clock.tick(60)
        
        # Handle AI
        if auto_play and not game.game_over and not game.victory:
            ai_timer += dt
            if ai_timer >= AI_DELAY:
                ai_timer = 0
                move = ai.step()
                if move:
                    action, r, c = move
                    if action == 'reveal':
                        game.reveal(r, c)
                    elif action == 'flag':
                        if not game.cells[(r, c)].is_flagged:
                            game.toggle_flag(r, c)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
                
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_a:
                    auto_play = not auto_play
                elif event.key == pygame.K_p:
                    show_probs = not show_probs
                elif event.key == pygame.K_s and not auto_play:
                    if not game.game_over and not game.victory:
                        move = ai.step()
                        if move:
                            action, r, c = move
                            if action == 'reveal':
                                game.reveal(r, c)
                            elif action == 'flag':
                                if not game.cells[(r, c)].is_flagged:
                                    game.toggle_flag(r, c)
                elif event.key == pygame.K_r:
                    game, ai = reset_game(game.level, game.shape, renderer)
                    screen = pygame.display.set_mode(renderer.get_window_size(game))
                    auto_play = False
                elif event.key == pygame.K_q:
                    game, ai = reset_game(game.level, 'square', renderer)
                    screen = pygame.display.set_mode(renderer.get_window_size(game))
                    auto_play = False
                elif event.key == pygame.K_h:
                    game, ai = reset_game(game.level, 'hexagon', renderer)
                    screen = pygame.display.set_mode(renderer.get_window_size(game))
                    auto_play = False
                elif event.key == pygame.K_1:
                    game, ai = reset_game('beginner', game.shape, renderer)
                    screen = pygame.display.set_mode(renderer.get_window_size(game))
                    auto_play = False
                elif event.key == pygame.K_2:
                    game, ai = reset_game('intermediate', game.shape, renderer)
                    screen = pygame.display.set_mode(renderer.get_window_size(game))
                    auto_play = False
                elif event.key == pygame.K_3:
                    game, ai = reset_game('expert', game.shape, renderer)
                    screen = pygame.display.set_mode(renderer.get_window_size(game))
                    auto_play = False
                elif event.key == pygame.K_4:
                    game, ai = reset_game('professional', game.shape, renderer)
                    screen = pygame.display.set_mode(renderer.get_window_size(game))
                    auto_play = False
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                
                if hasattr(renderer, 'restart_rect') and renderer.restart_rect.collidepoint(pos):
                    if event.button == 1:
                        game, ai = reset_game(game.level, game.shape, renderer)
                        screen = pygame.display.set_mode(renderer.get_window_size(game))
                        auto_play = False
                    continue
                
                if not auto_play:
                    cell = renderer.get_cell_from_mouse(pos, game)
                    if cell:
                        r, c = cell
                        if event.button == 1:
                            game.reveal(r, c)
                        elif event.button == 3:
                            game.toggle_flag(r, c)
                        elif event.button == 2:
                            game.toggle_chord(r, c)

        # Before drawing, always ensure we have probabilities calculated if requested
        if show_probs and not game.first_click and not game.game_over and not game.victory:
            ai.calculate_probabilities()

        # Update hover cell for visual feedback
        renderer.set_hover(pygame.mouse.get_pos(), game)

        renderer.draw(screen, game, ai.probabilities, auto_play, show_probs)
        pygame.display.flip()

if __name__ == "__main__":
    main()
