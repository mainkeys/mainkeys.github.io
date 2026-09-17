/* SPDX-License-Identifier: BSD-2-Clause */
#ifndef SERIES_ECHO_TA_H
#define SERIES_ECHO_TA_H

#define SERIES_ECHO_UUID \
    { 0x4d5acb20, 0x46c2, 0x4bc7, \
      { 0x9c, 0x0d, 0x58, 0xf5, 0x0a, 0x11, 0x79, 0xd2 } }

/* INPUT memref, OUTPUT memref, NONE, NONE; lengths count bytes, not NUL. */
#define SERIES_CMD_ECHO 0
/* VALUE_INOUT, NONE, NONE, NONE; increment a modulo 2^32, preserve b. */
#define SERIES_CMD_VALUE 1

#endif
