import pygame

def text_to_screen(screen, text, x, y, size = 30,
        color = (0, 0, 0), font_type = pygame.font.match_font("")):
    try:
        text = str(text)
        font = pygame.font.Font(font_type, size)
        text = font.render(text, True, color)
        screen.blit(text, (x, y))

    except Exception, e:
        print 'Font Error, saw it coming'
        raise e
