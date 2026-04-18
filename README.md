<<<<<<< HEAD
# Box Blast - Gesture Controlled Infinite Brick Breaker

A Python game that uses your webcam hand gestures to control the paddle and launch the ball.

## Tech Stack
- Pygame: rendering, collisions, gameplay loop
- MediaPipe: hand tracking and pinch detection
- OpenCV: webcam capture

## Controls
- Hand movement: move your palm left and right to control paddle position
- Pinch throw: touch thumb tip and index tip to throw the ball
- Keyboard fallback:
  - Left / Right (or A / D): paddle movement
  - Space: throw ball
  - Esc: quit

## Gesture Logic
- Paddle follows landmark 0 (palm center/base) normalized x in range 0.0 to 1.0
- Throw trigger when distance between landmarks 4 and 8 is less than 0.05

## Gameplay
- Ball bounces off left, right, and top walls
- Missing the ball at bottom loses 1 life (3 total)
- Each box has health; collision decreases health by 1
- Box is removed only when health reaches 0
- When all boxes are cleared, a harder level is generated automatically

## Install

pip install -r requirements.txt

If you previously installed a newer MediaPipe and get:

AttributeError: module 'mediapipe' has no attribute 'solutions'

run:

pip install --upgrade --force-reinstall -r requirements.txt

## Run

python main.py

## UI Tuning

- Camera feed area is fixed in a dedicated right panel via `CAMERA_RECT` in `main.py`.
- To move or resize camera feed, edit `CAMERA_RECT = pygame.Rect(x, y, width, height)`.
- Level 1 box count is controlled in `generate_level()` using:
  - `rows = min(6, 2 + level_number // 2)`
  - `cols = min(9, 6 + (level_number - 1) // 2)`
  This starts level 1 at 12 boxes and scales up gradually with each level.
=======
# Box-Blast
Box Blast is a gesture-powered brick breaker game built with Python, Pygame, OpenCV, and MediaPipe. Move the paddle with your hand, pinch to launch the ball, smash health-based boxes, chain combos, and survive neon-styled levels.
>>>>>>> 8a41551b7c90f3f01e41325546084ee75477bc96
