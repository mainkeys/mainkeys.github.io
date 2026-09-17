/* SPDX-License-Identifier: BSD-2-Clause */
#ifndef USER_TA_HEADER_DEFINES_H
#define USER_TA_HEADER_DEFINES_H
#include <series_echo_ta.h>
#define TA_UUID SERIES_ECHO_UUID
#define TA_FLAGS 0
#define TA_STACK_SIZE (4 * 1024)
#define TA_DATA_SIZE (32 * 1024)
#define TA_VERSION "1.0"
#define TA_DESCRIPTION "Byte echo for the public TEE learning series"
#endif
