"""Parse guest markers without changing the original serial recording."""
# SPDX-License-Identifier: BSD-2-Clause
import base64
import re

# Guest CRLF may pass through a host PTY with ONLCR, becoming CRCRLF.
STATUS_PATTERN = r"__LAB_STATUS=([0-9]+)\r*\n"
FILE_PATTERN = r"__FILE_BEGIN__\r*\n(.*?)\r*\n__FILE_END__"


def decode_guest_file(output):
    match = re.search(FILE_PATTERN, output, re.S)
    if not match:
        raise ValueError("Missing guest file markers")
    return base64.b64decode(re.sub(r"\s", "", match.group(1)), validate=True)
