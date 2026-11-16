# Explore check (Boss, with the pad)

Explore is the first mode the robot drives by itself. It cruises slowly (0.3). When something is within 40 cm ahead, it stops, looks left and right with the sensor, turns toward the open side, and goes on. It veers away from a wall it is passing at a shallow angle. The obstacle guard still limits every move. Write a result after each step.

The Y button is the yellow top button. If nothing happens, run `tools/bench pad-check` and press Y: the line should say `KEY BTN_Y` (or `BTN_WEST`).

## On the stand (wheels off the ground)

1. Press Start, then Y. The wheels turn forward slowly and the sensor fans left and right.
   Result:
2. Hold a hand about 30 cm in front of the sensor. The wheels stop, the sensor sweeps fully left and right, then the wheels spin the robot one way. Move your hand away: they go back to forward.
   Result:
3. Push a stick: manual control comes back at once. Press Y again, then Back: everything stops.
   Result:

## On the floor (a room with some space, kill switch in reach)

4. Press Start, then Y, and let it explore for 2 minutes. Does it turn away before touching walls and furniture? Note what it hits, if anything. Chair legs and soft things are hard for an ultrasonic sensor.
   Result:
5. While it explores, push a stick: it stops exploring and follows the pad.
   Result:
6. Open the status page during the run: the radar shows the fan and the sweeps.
   Result:
