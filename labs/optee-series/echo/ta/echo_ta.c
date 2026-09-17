/* SPDX-License-Identifier: BSD-2-Clause */
#include <tee_internal_api.h>
#include <tee_internal_api_extensions.h>
#include <series_echo_ta.h>

TEE_Result TA_CreateEntryPoint(void)
{
    return TEE_SUCCESS;
}

void TA_DestroyEntryPoint(void)
{
}

TEE_Result TA_OpenSessionEntryPoint(uint32_t types, TEE_Param params[4],
                                   void **session)
{
    (void)params;
    if (types != TEE_PARAM_TYPES(TEE_PARAM_TYPE_NONE, TEE_PARAM_TYPE_NONE,
                                TEE_PARAM_TYPE_NONE, TEE_PARAM_TYPE_NONE))
        return TEE_ERROR_BAD_PARAMETERS;
    *session = NULL;
    IMSG("series-echo: session opened");
    return TEE_SUCCESS;
}

void TA_CloseSessionEntryPoint(void *session)
{
    (void)session;
}

static TEE_Result echo_bytes(uint32_t types, TEE_Param params[4])
{
    size_t required;
    size_t capacity;

    if (types != TEE_PARAM_TYPES(TEE_PARAM_TYPE_MEMREF_INPUT,
                                TEE_PARAM_TYPE_MEMREF_OUTPUT,
                                TEE_PARAM_TYPE_NONE, TEE_PARAM_TYPE_NONE))
        return TEE_ERROR_BAD_PARAMETERS;

    required = params[0].memref.size;
    capacity = params[1].memref.size;
    if ((required && !params[0].memref.buffer) ||
        (capacity && !params[1].memref.buffer))
        return TEE_ERROR_BAD_PARAMETERS;

    params[1].memref.size = required;
    if (capacity < required)
        return TEE_ERROR_SHORT_BUFFER;
    if (required)
        TEE_MemMove(params[1].memref.buffer, params[0].memref.buffer, required);
    return TEE_SUCCESS;
}

TEE_Result TA_InvokeCommandEntryPoint(void *session, uint32_t command,
                                     uint32_t types, TEE_Param params[4])
{
    (void)session;
    switch (command) {
    case SERIES_CMD_ECHO:
        return echo_bytes(types, params);
    case SERIES_CMD_VALUE:
        if (types != TEE_PARAM_TYPES(TEE_PARAM_TYPE_VALUE_INOUT,
                                    TEE_PARAM_TYPE_NONE,
                                    TEE_PARAM_TYPE_NONE, TEE_PARAM_TYPE_NONE))
            return TEE_ERROR_BAD_PARAMETERS;
        params[0].value.a += 1;
        return TEE_SUCCESS;
    default:
        return TEE_ERROR_NOT_SUPPORTED;
    }
}
