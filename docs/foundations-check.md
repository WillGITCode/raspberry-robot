# Foundations check (Boss, with the pad)

What changed since the first floor run, and a short check for each. Agents checked the logic with fake pins and ran the sensors on the bench; this is the part only the pad and the floor can prove. Write a result after each step.

**What is new**

- **Car steering, left stick:** push it sideways and the robot arcs forward. At full deflection the outer side runs full and the inner side half. Pulled back, the robot reverses and arcs the way a car backs. The right stick still spins in place. The cap is 0.3; the right trigger still boosts to 1.0.
- **Soft starts:** speeding up takes about 0.25 s from 0 to full. Slowing and stopping are immediate.
- **Obstacle guard:** the ping looks ahead 25 times a second. Forward speed drops from 60 cm and reaches zero at 20 cm. Reverse and spinning always work, so you can back off or turn away. With no reading, forward speed stays at 0.3 and boost is off.
- **Status page:** open `http://<the Pi's address>:8080/` on the desktop or your phone. It shows the mode, the command, the guard, a radar of the ping, CPU temperature and power flags.

## On the stand (wheels off the ground)

1. Press Start. Push the left stick fully left: the right wheels spin faster than the left wheels, and both turn forward.
   Result:
2. Fully right: the opposite.
   Result:
3. Halfway left: a gentler difference. Then left stick back and left: both sides reverse, with the left side slower.
   Result:
4. Right stick: it spins in place as before.
   Result:
5. Hold a hand about 15 cm in front of the ping and push the left stick forward: the wheels stop. Pull your hand away: they start again.
   Result:

## On the floor (clear 2 m, kill switch in reach)

6. Drive forward slowly at a wall or a box: the robot slows, then stops about 20 cm short. Back off with the stick pulled back.
   Result:
7. Drive in a wide left arc, then a wide right one. Say how the steering feels: too sharp, too gentle, or right.
   Result:
8. Open the status page during the drive: the radar shows the wall, and power shows `ok`.
   Result:
