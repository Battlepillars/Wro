import pygame
import sys
import time

pygame.init()
WIDTH, HEIGHT = 300, 100
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Stoppuhr")

font = pygame.font.SysFont(None, 48)
start_time = pygame.time.get_ticks()  # Millisekunden seit pygame.init()

clock = pygame.time.Clock()

while True:
  for event in pygame.event.get():
    if event.type == pygame.QUIT:
      pygame.quit()
      sys.exit()

  elapsed = (pygame.time.get_ticks() - start_time) / 1000.0  # Umrechnung von ms zu Sekunden
  mins = int(elapsed // 60)
  secs = int(elapsed % 60)
  millis = int((elapsed - int(elapsed)) * 100)
  time_str = f"{mins:02}:{secs:02}"

  screen.fill((30, 30, 30))
  text = font.render(time_str, True, (255, 255, 255))
  rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
  screen.blit(text, rect)

  pygame.display.flip()
  clock.tick(1)