/* SPDX-License-Identifier: BSD-2-Clause */
#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <tee_client_api.h>
#include <series_echo_ta.h>

static int check_result(const char *name, TEEC_Result result, uint32_t origin,
                        TEEC_Result expected)
{
    printf("%s: result=0x%08" PRIx32 " origin=%" PRIu32 "\n",
           name, result, origin);
    if (result != expected) {
        fprintf(stderr, "%s: expected 0x%08" PRIx32 "\n", name, expected);
        return 0;
    }
    /* Only assert the origin of the deliberate TA errors. No assumption is
     * made about success origins or errors raised by libteec/driver/core. */
    if (expected != TEEC_SUCCESS && origin != TEEC_ORIGIN_TRUSTED_APP) {
        fprintf(stderr, "%s: failure did not originate in the TA\n", name);
        return 0;
    }
    return 1;
}

static void prepare_echo(TEEC_Operation *op, void *input, size_t length,
                         void *output, size_t capacity)
{
    memset(op, 0, sizeof(*op));
    op->paramTypes = TEEC_PARAM_TYPES(TEEC_MEMREF_TEMP_INPUT,
                                     TEEC_MEMREF_TEMP_OUTPUT,
                                     TEEC_NONE, TEEC_NONE);
    op->params[0].tmpref.buffer = input;
    op->params[0].tmpref.size = length;
    op->params[1].tmpref.buffer = output;
    op->params[1].tmpref.size = capacity;
}

static int run_tests(TEEC_Session *session)
{
    unsigned char input[] = "hello from CA";
    unsigned char output[32];
    unsigned char sentinel[sizeof(output)];
    const size_t length = sizeof(input) - 1; /* Protocol excludes trailing NUL. */
    TEEC_Operation op;
    TEEC_Result result;
    uint32_t origin;

    memset(output, 0xa5, sizeof(output));
    prepare_echo(&op, input, length, output, sizeof(output));
    origin = 0;
    result = TEEC_InvokeCommand(session, SERIES_CMD_ECHO, &op, &origin);
    if (!check_result("normal", result, origin, TEEC_SUCCESS) ||
        op.params[1].tmpref.size != length ||
        memcmp(input, output, length) || output[length] != 0xa5)
        return 0;
    printf("echo bytes (%zu): %.*s\n", length, (int)length, (char *)output);

    /* Valid backing pointers with zero size avoid testing a separate NULL
     * memref capability. The contract is a zero-byte input and output. */
    prepare_echo(&op, input, 0, output, 0);
    origin = 0;
    result = TEEC_InvokeCommand(session, SERIES_CMD_ECHO, &op, &origin);
    if (!check_result("zero-length", result, origin, TEEC_SUCCESS) ||
        op.params[1].tmpref.size != 0)
        return 0;

    memset(output, 0xa5, sizeof(output));
    memcpy(sentinel, output, sizeof(output));
    prepare_echo(&op, input, length, output, 3);
    origin = 0;
    result = TEEC_InvokeCommand(session, SERIES_CMD_ECHO, &op, &origin);
    if (!check_result("short-buffer", result, origin, TEEC_ERROR_SHORT_BUFFER) ||
        op.params[1].tmpref.size != length ||
        memcmp(output, sentinel, sizeof(output)))
        return 0;
    printf("short-buffer required bytes: %zu\n", op.params[1].tmpref.size);

    prepare_echo(&op, input, length, output, sizeof(output));
    op.paramTypes = TEEC_PARAM_TYPES(TEEC_VALUE_INPUT, TEEC_MEMREF_TEMP_OUTPUT,
                                    TEEC_NONE, TEEC_NONE);
    op.params[0].value.a = 7;
    op.params[0].value.b = 9;
    origin = 0;
    result = TEEC_InvokeCommand(session, SERIES_CMD_ECHO, &op, &origin);
    if (!check_result("wrong-type", result, origin, TEEC_ERROR_BAD_PARAMETERS))
        return 0;

    memset(&op, 0, sizeof(op));
    op.paramTypes = TEEC_PARAM_TYPES(TEEC_VALUE_INOUT, TEEC_NONE,
                                    TEEC_NONE, TEEC_NONE);
    op.params[0].value.a = 41;
    op.params[0].value.b = 99;
    origin = 0;
    result = TEEC_InvokeCommand(session, SERIES_CMD_VALUE, &op, &origin);
    if (!check_result("value", result, origin, TEEC_SUCCESS) ||
        op.params[0].value.a != 42 || op.params[0].value.b != 99)
        return 0;
    return 1;
}

int main(void)
{
    TEEC_Context context;
    TEEC_Session session;
    const TEEC_UUID uuid = SERIES_ECHO_UUID;
    TEEC_Result result;
    uint32_t origin = 0;
    int passed;

    result = TEEC_InitializeContext(NULL, &context);
    if (result != TEEC_SUCCESS) {
        fprintf(stderr, "InitializeContext: 0x%08" PRIx32 "\n", result);
        return EXIT_FAILURE;
    }
    result = TEEC_OpenSession(&context, &session, &uuid, TEEC_LOGIN_PUBLIC,
                              NULL, NULL, &origin);
    if (result != TEEC_SUCCESS) {
        fprintf(stderr, "OpenSession: 0x%08" PRIx32 " origin=%" PRIu32 "\n",
                result, origin);
        TEEC_FinalizeContext(&context);
        return EXIT_FAILURE;
    }
    passed = run_tests(&session);
    TEEC_CloseSession(&session);
    TEEC_FinalizeContext(&context);
    puts(passed ? "PASS: 5 cases" : "FAIL: see result and origin above");
    return passed ? EXIT_SUCCESS : EXIT_FAILURE;
}
