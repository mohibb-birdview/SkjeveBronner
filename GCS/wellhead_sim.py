import numpy as np
import random
import time


class Wellhead:
    def __init__(self, *argv):
        self.pos = (0, 0)

        self.k = 2

        self.n = np.arange(self.k) + 1

        self.x_rand = np.random.random(self.k) * 2 * np.pi
        self.y_rand = np.random.random(self.k) * 2 * np.pi

        self.x_freq = np.multiply(1/6, self.n)
        self.y_freq = np.multiply(1/6, self.n)

        x_max = random.random() + 1
        y_max = random.random() + 1
        self.x_amp = np.divide(1, self.n)
        self.y_amp = np.divide(1, self.n)

        self.x_amp = self.x_amp / sum(self.x_amp) * x_max
        self.y_amp = self.y_amp / sum(self.y_amp) * y_max

        self.last_t = 0

    def get_positions(self, t=None):
        if t is None:
            t = time.time()

        x = 0
        y = 0
        for i in range(self.k):
            x += self.x_amp[i] * np.sin(self.x_freq[i] * t + self.x_rand[i])
            y += self.y_amp[i] * np.sin(self.y_freq[i] * t + self.y_rand[i])

        """x = 1 / k * self.x_amp * np.sin(self.x_freq * t + self.x_rand) + \
            1 / k * self.x_amp * np.sin(self.x_freq / 2 * t + self.x_rand) + \
            1 / k * self.x_amp * np.sin(self.x_freq / 3 * t + self.x_rand)

        y = 1 / k * self.y_amp * np.sin(self.y_freq * t + self.y_rand) + \
            1 / k * self.y_amp * np.sin(self.y_freq / 2 * t + self.y_rand) + \
            1 / k * self.y_amp * np.sin(self.y_freq / 2 * t + self.y_rand)
        """

        self.y = int(y * 1000)
        self.x = int(x * 1000)

        self.pos = (x, y)

        return self.pos

if __name__ == '__main__':
    w = Wellhead()

    while True:
        print(w.get_positions())
        time.sleep(0.1)
