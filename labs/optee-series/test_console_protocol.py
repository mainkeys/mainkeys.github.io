"""Regress the double-CR failure observed in Actions run 35250383576."""
# SPDX-License-Identifier: BSD-2-Clause
import base64
import re
import unittest

from console_protocol import STATUS_PATTERN, decode_guest_file


class ConsoleProtocolTests(unittest.TestCase):
    def test_observed_status_marker(self):
        # Extracted from the failed run's unmodified UART byte stream.
        output = "105\r\r\n\r\r\n__LAB_STATUS=0\r\r\nSERIES_READY# "
        self.assertEqual(re.search(STATUS_PATTERN, output).group(1), "0")

    def test_status_and_file_line_endings(self):
        payload = b"a trace line\r\n\x00\xff\nsecond line\n"
        encoded = base64.b64encode(payload).decode("ascii")
        for newline in ("\n", "\r\n", "\r\r\n"):
            with self.subTest(newline=repr(newline)):
                status = "__LAB_STATUS=17" + newline + "SERIES_READY# "
                self.assertEqual(int(re.search(STATUS_PATTERN, status).group(1)), 17)
                output = "__FILE_BEGIN__" + newline + encoded + newline + newline + "__FILE_END__" + newline
                self.assertEqual(decode_guest_file(output), payload)

    def test_missing_or_invalid_file_is_rejected(self):
        with self.assertRaises(ValueError):
            decode_guest_file("base64: file missing\r\r\n")
        with self.assertRaises(ValueError):
            decode_guest_file("__FILE_BEGIN__\r\r\nnot-base64!\r\r\n__FILE_END__")


if __name__ == "__main__":
    unittest.main()
