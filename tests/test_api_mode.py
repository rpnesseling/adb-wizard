import unittest

from adbw.api import parse_params


class TestApiMode(unittest.TestCase):
    def test_parse_params_json(self) -> None:
        params = parse_params('{"package":"com.example","third_party":true}')
        self.assertEqual(params["package"], "com.example")
        self.assertEqual(params["third_party"], "True")

    def test_parse_params_kv(self) -> None:
        params = parse_params("command=getprop ro.build.version.release,third_party=true")
        self.assertEqual(params["command"], "getprop ro.build.version.release")
        self.assertEqual(params["third_party"], "true")


if __name__ == "__main__":
    unittest.main()

