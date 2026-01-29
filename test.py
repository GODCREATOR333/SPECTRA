import pygame
import math

# --- Pygame setup ---
pygame.init()
screen = pygame.display.set_mode((800, 600))
clock = pygame.time.Clock()

# --- Parameters ---
n = 10        # number of points on base polygon
z =100      # number of iterations
h = -50       # perpendicular height for spikes
cx, cy = screen.get_width() // 2, screen.get_height() // 2
r = 150       # radius of initial circle

# --- Zoom parameters ---
zoom = 1.0
zoom_step = 0.1

# --- Generate initial polygon points on circle ---
points = []
for i in range(n):
    theta = 2 * math.pi * i / n
    x = cx + r * math.cos(theta)
    y = cy + r * math.sin(theta)
    points.append((x, y))

# --- Utility function to scale a point relative to center ---
def scale_point(p, center, zoom):
    cx, cy = center
    x = cx + (p[0] - cx) * zoom
    y = cy + (p[1] - cy) * zoom
    return (int(x), int(y))

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # --- Zoom control ---
    keys = pygame.key.get_pressed()
    if keys[pygame.K_UP]:
        zoom += zoom_step
    if keys[pygame.K_DOWN]:
        zoom = max(0.1, zoom - zoom_step)

    screen.fill((0, 0, 0))

    # Scale base points
    scaled_points = [scale_point(p, (cx, cy), zoom) for p in points]

    # Draw reference circle (scaled)
    pygame.draw.circle(screen, (60, 60, 60), (cx, cy), int(r * zoom), 1)

    # Draw base polygon points
    for p in scaled_points:
        pygame.draw.circle(screen, (255, 0, 0), p, 3)

    # --- Iterative fractal spike generation ---
    current_points = scaled_points.copy()  # start with base polygon

    for iteration in range(z):
        perp_points = []

        for i in range(len(current_points)):
            p1 = current_points[i]
            p2 = current_points[(i + 1) % len(current_points)]

            # Edge vector
            dx = p2[0] - p1[0]
            dy = p2[1] - p1[1]

            # Midpoint
            mx = (p1[0] + p2[0]) / 2
            my = (p1[1] + p2[1]) / 2

            # Perpendicular unit vector
            length = math.hypot(dx, dy)
            if length == 0:
                continue
            ux = -dy / length
            uy = dx / length

            # Point at height h from midpoint (apply zoom)
            px = int(mx + ux * h * zoom)
            py = int(my + uy * h * zoom)

            # Draw lines from edge endpoints to perpendicular tip
            pygame.draw.line(screen, (255, 255, 255), p1, (px, py), 2)
            pygame.draw.line(screen, (255, 255, 255), p2, (px, py), 2)

            # Store perpendicular tip
            perp_points.append((px, py))

        # Connect perpendicular tips to form next polygon layer
        for i in range(len(perp_points)):
            pygame.draw.line(screen, (255, 255, 0),
                             perp_points[i],
                             perp_points[(i + 1) % len(perp_points)], 2)

        # Next iteration polygon
        current_points = perp_points.copy()

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
