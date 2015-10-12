#!/usr/bin/env python
import unittest
# from droopy_web import app
from droopy_web import is_colinear, orientation, untangle


class FlaskTestCase(unittest.TestCase):
    colinear_points = [((0, 0), (1, 1), (2, 2), (3, 3)),
                       ((0, 0), (1, 1), (2, 2), (2, 2))]

    non_colinear_points = [((0, 0), (1, 1), (2, 2), (2, 3)),
                           ((0, 0), (1, 1), (0, 0), (1, 3))]

    ccw_points = [((0, 0), (1, 0), (1, 1)),
                  ((0, 0), (0, 1), (-1, 0)),
                  ((0, 0), (-1, 0), (0, -1)),
                  ((91, 51), (89, 47), (90, 48))]

    cw_points = [((0, 0), (1, 0), (1, -1)),
                 ((0, 0), (0, 1), (1, 1)),
                 ((0, 0), (-1, 0), (-1, 1))]

    untangle_path = [(0, 0), (0, 0), (1, 1), (2, 2), (1, 3), (0, 3), (4, 0)]
    untangled_path = [(0, 0), (0, 0), (1, 1), (0, 3), (1, 3), (2, 2), (4, 0)]

    def test_is_colinear(self):
        for a, b, c, d in self.colinear_points:
            self.assertTrue(is_colinear((a, b), (c, d)))

        for a, b, c, d in self.non_colinear_points:
            self.assertFalse(is_colinear((a, b), (c, d)))

    def test_orientation(self):
        for a, b, c in self.cw_points:
            self.assertEqual(orientation(a, b, c), -1)
        for a, b, c in self.ccw_points:
            self.assertEqual(orientation(a, b, c), 1)
        for a, b, c, d in self.colinear_points:
            self.assertEqual(orientation(a, b, c), 0)

    def test_bounding_boxes(self):
        pass

    def test_untabngle_path(self):
        self.assertEqual(untangle(self.untangle_path), self.untangled_path)

if __name__ == '__main__':
    unittest.main()
