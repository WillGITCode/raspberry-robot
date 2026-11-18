"""GY-521 (MPU-6050) gyro over I2C with smbus2: the yaw rate for the robot's heading.

NOT FITTED YET: it needs I2C on (dtparam=i2c_arm=on), the servo moved off BOARD 5 (the I2C clock
pin) to BOARD 12, and a place on the deck (hardware/wiring.md, hardware/gy-521/spec.md). The service
starts it only with ROVER_IMU=1. Register map from the MPU-6050 datasheet: wake with PWR_MGMT_1 = 0,
gyro full scale +-250 deg/s (131 counts per deg/s), digital low-pass filter about 44 Hz.
"""
import math

BUS = 1
ADDRESS = 0x68
PWR_MGMT_1, CONFIG, GYRO_CONFIG, GYRO_ZOUT_H, WHO_AM_I = 0x6B, 0x1A, 0x1B, 0x47, 0x75
COUNTS_PER_DPS = 131.0


def to_signed(hi, lo):
    v = hi << 8 | lo
    return v - 65536 if v & 0x8000 else v


class Mpu6050:
    def __init__(self, bus=BUS, address=ADDRESS):
        from smbus2 import SMBus

        self.bus, self.address = SMBus(bus), address
        who = self.bus.read_byte_data(address, WHO_AM_I)
        if who not in (0x68, 0x98, 0x70, 0x72):  # clones answer with other ids
            raise OSError(f"no MPU-6050 at 0x{address:02x} (WHO_AM_I 0x{who:02x})")
        self.bus.write_byte_data(address, PWR_MGMT_1, 0x00)
        self.bus.write_byte_data(address, CONFIG, 0x03)
        self.bus.write_byte_data(address, GYRO_CONFIG, 0x00)
        self.bias = 0.0

    def raw_yaw_rate(self):
        hi, lo = self.bus.read_i2c_block_data(self.address, GYRO_ZOUT_H, 2)
        return math.radians(to_signed(hi, lo) / COUNTS_PER_DPS)

    def yaw_rate(self):
        """rad/s, counter-clockwise (left) positive, bias removed. One 2-byte I2C read."""
        return self.raw_yaw_rate() - self.bias

    def close(self):
        self.bus.close()


class BiasCalibrator:
    """Averages the yaw rate while the robot is still (motors coasting) to cancel the gyro's drift."""

    def __init__(self, samples=100):
        self.samples, self._sum, self._n = samples, 0.0, 0

    def add(self, raw):
        if self._n < self.samples:
            self._sum += raw
            self._n += 1

    @property
    def done(self):
        return self._n >= self.samples

    @property
    def bias(self):
        return self._sum / self._n if self._n else 0.0


class FakeImu:
    def __init__(self, rate=0.0, bias=0.0):
        self.rate, self.bias = rate, 0.0
        self._true_bias = bias

    def raw_yaw_rate(self):
        return self.rate + self._true_bias

    def yaw_rate(self):
        return self.raw_yaw_rate() - self.bias

    def close(self):
        pass
