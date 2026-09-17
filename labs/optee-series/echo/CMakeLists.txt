# SPDX-License-Identifier: BSD-2-Clause
project(optee_series_echo C)
add_executable(optee_series_echo host/main.c)
target_compile_features(optee_series_echo PRIVATE c_std_99)
target_compile_options(optee_series_echo PRIVATE -Wall -Wextra)
target_include_directories(optee_series_echo PRIVATE ta/include)
target_link_libraries(optee_series_echo PRIVATE teec)
install(TARGETS optee_series_echo DESTINATION ${CMAKE_INSTALL_BINDIR})
