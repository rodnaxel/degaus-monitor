import unittest

import proxy


class TestPatternHandler(unittest.TestCase):
    def setUp(self):
        self.pattern = ['Max', 'Min', 'Null', "L", "Max", "Min", "L"]
        self.input_data = [153, 0, 0, 0, 0, 0]

    def test_handle_43(self):
        n_channels = 6
        handler = proxy.PatternHandler(self.pattern, n_channels)
        res = ['Max', 'Min', 'Null', 153, "Max", "Min"]
        self.assertEqual(res, handler(self.input_data))

    def test_handle_150(self):
        n_channels = 4
        handler = proxy.PatternHandler(self.pattern, n_channels)
        res = ['Max', 'Min', 'Null', 153]
        self.assertEqual(res, handler(self.input_data))

class TestVoltageHandler(unittest.TestCase):
    def setUp(self):
        self.input_data = [-300, -100, -50, 0, -100, -300]

    def test_handle_i10(self):
        handler = proxy.VoltageHandler(imax=9.99, ku=1)
        #res = [-12, -4, -2, 0, -4, -12]
        [-12, -4, -2, 0, -4, -12]
        self.assertEqual(res, handler(self.input_data))

    def test_handle_i55(self):
        handler = proxy.VoltageHandler(imax=54.59, ku=1)
        res = [-67, -22, -11, 0, -22, -67]
        self.assertEqual(res, handler(self.input_data))


if __name__ == "__main__":
    unittest.main()
