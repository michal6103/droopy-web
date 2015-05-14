import unittest
# from droopy_web import app
from droopy_web import is_colinear


class FlaskTestCase(unittest.TestCase):
    colinear_points = [((0, 0), (1, 1), (2, 2), (3, 3)),
                       ((0, 0), (1, 1), (2, 2), (2, 2))]

    non_colinear_points = [((0, 0), (1, 1), (2, 2), (2, 3)),
                           ((0, 0), (1, 1), (0, 0), (1, 3))]

    def test_is_colinear(self):
        for a, b, c, d in self.colinear_points:
            print("a: {}\t b:{}\tc:{}\td:{}".format(a, b, c, d))
            self.assertTrue(is_colinear((a, b), (c, d)))

        for a, b, c, d in self.non_colinear_points:
            print("a: {}\t b:{}\tc:{}\td:{}".format(a, b, c, d))
            self.assertFalse(is_colinear((a, b), (c, d)))


if __name__ == '__main__':
    unittest.main()
