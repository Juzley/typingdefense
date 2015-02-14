"""Typing Defense - Camera module."""
import numpy as np
import math
from typingdefense.vector import Vector


class Camera(object):

    """A camera class, implements camera and perspective transformations."""

    def __init__(self, origin, target, up,
                 fov, screen_width, screen_height, near, far):
        self.origin = np.array(origin, np.float32)
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.near = near
        self.far = far

        self.forward = np.array(target, np.float32) - origin
        self.forward = self.forward / np.linalg.norm(self.forward)

        self.up = up / np.linalg.norm(up)

        # TODO: Do something if we're looking straight up or straight down
        self.right = np.cross(self.forward, self.up)
        self.right = self.right / np.linalg.norm(self.right)

        rot = np.matrix([[self.right[0], self.right[1], self.right[2], 0],
                         [self.up[0], self.up[1], self.up[2], 0],
                         [self.forward[0], self.forward[1], self.forward[2], 0],
                         [0, 0, 0, 1]], np.float32)
        trans = np.matrix([[1, 0, 0, -origin[0]],
                           [0, 1, 0, -origin[1]],
                           [0, 0, 1, -origin[2]],
                           [0, 0, 0, 1]], np.float32)
        self.cam_matrix = rot * trans

        ratio = screen_width / screen_height
        tanHalfFov = math.tan(math.radians(fov / 2.0))
        zRange = near - far
        self.proj_matrix = np.matrix(
            [[1 / (tanHalfFov * ratio), 0, 0, 0],
             [0, 1 / tanHalfFov, 0, 0],
             [0, 0, (-near - far) / zRange, 2 * far * near / zRange],
             [0, 0, 1, 0]], np.float32)

        self.trans_matrix = self.proj_matrix * self.cam_matrix

    def unproject(self, screen_coords, world_z):
        # Convert from screen coords to NDCs
        x = screen_coords.x * 2 / self.screen_width - 1
        y = screen_coords.y * 2 / self.screen_height - 1

        inv_trans = np.linalg.inv(self.trans_matrix)
        near_coords = np.array([[x], [y], [0], [1]])
        far_coords = np.array([[x], [y], [1], [1]])

        world_near = inv_trans * near_coords
        world_far = inv_trans * far_coords

        # Perspective divide
        world_near /= world_near[3, 0]
        world_far /= world_far[3, 0]

        world_neartofar = world_far - world_near
        ratio = (world_z - world_near[2, 0]) / world_neartofar[2, 0]

        return Vector(world_near[0, 0] + (world_neartofar[0, 0] * ratio),
                      world_near[1, 0] + (world_neartofar[1, 0] * ratio),
                      world_near[2, 0] + (world_neartofar[2, 0] * ratio))

    def trans_matrix_as_array(self):
        return np.asarray(self.trans_matrix).reshape(-1)
