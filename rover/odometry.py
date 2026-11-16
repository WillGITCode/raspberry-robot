"""Pose (x, y, heading) from the encoders and the gyro. Dead reckoning: it drifts, a map corrects it.

Distance comes from the front encoders, signed by each side's motor output. Heading comes from the
gyro when there is one; on a 4WD skid-steer robot the wheels slip in turns, so heading from the
encoders needs a measured effective track (`track_m`) and is only a fallback.
"""
import math

from rover.encoders import M_PER_EDGE


class Odometry:
    def __init__(self, track_m=None, m_per_edge=M_PER_EDGE):
        self.track_m, self.m_per_edge = track_m, m_per_edge
        self.x = self.y = self.heading = 0.0
        self.distance = 0.0  # total path length, metres
        self.speed = (0.0, 0.0)  # m/s per side, signed
        self._sign = [1.0, 1.0]

    def update(self, edges, output, dt, yaw_rate=None):
        """edges: (left, right) counts this tick; output: the motor output (left, right) this tick."""
        for i, o in enumerate(output):
            if o:
                self._sign[i] = 1.0 if o > 0 else -1.0  # coasting keeps the last direction
        dl = edges[0] * self.m_per_edge * self._sign[0]
        dr = edges[1] * self.m_per_edge * self._sign[1]
        if dt > 0:
            self.speed = (dl / dt, dr / dt)
        d = (dl + dr) / 2
        if yaw_rate is not None:
            dth = yaw_rate * dt
        elif self.track_m:
            dth = (dr - dl) / self.track_m
        else:
            dth = 0.0  # no heading source yet: straight-line distance only
        mid = self.heading + dth / 2
        self.x += d * math.cos(mid)
        self.y += d * math.sin(mid)
        self.heading = math.atan2(math.sin(self.heading + dth), math.cos(self.heading + dth))
        self.distance += abs(d)

    def pose(self):
        return {"x": round(self.x, 3), "y": round(self.y, 3), "heading_deg": round(math.degrees(self.heading), 1),
                "distance": round(self.distance, 3), "speed": [round(v, 3) for v in self.speed]}


class PoseTracker:
    """One call per tick after the motors: reads the encoders and the gyro, updates the pose.

    The gyro's bias is measured over its first samples while the motors coast, before any heading."""

    def __init__(self, encoders=None, imu=None, track_m=None, calibrator=None):
        from rover.imu import BiasCalibrator

        self.encoders, self.imu = encoders, imu
        self.odo = Odometry(track_m)
        self.cal = (calibrator or BiasCalibrator()) if imu is not None else None
        self._t = None

    def tick(self, now, output):
        dt = 0.0 if self._t is None else now - self._t
        self._t = now
        edges = self.encoders.read() if self.encoders is not None else (0, 0)
        yaw = None
        if self.imu is not None:
            raw = self.imu.raw_yaw_rate()
            if not self.cal.done:
                if tuple(output) == (0.0, 0.0):
                    self.cal.add(raw)
                if self.cal.done:
                    self.imu.bias = self.cal.bias
            else:
                yaw = raw - self.imu.bias
        self.odo.update(edges, output, dt, yaw)

    def close(self):
        for part in (self.encoders, self.imu):
            if part is not None:
                try:
                    part.close()
                except Exception:
                    pass
