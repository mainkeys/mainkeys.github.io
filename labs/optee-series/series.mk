# SPDX-License-Identifier: BSD-2-Clause
# Pass as a second -f file after the upstream qemu_v8.mk (see README).
# Variables affecting conditionals must be provided on make's command line;
# this file only adds evidence/run helper targets. Use series-make.sh.
.PHONY: series-config series-console
series-config:
	@printf '%s\n' 'SPMC_AT_EL=$(SPMC_AT_EL)' 'TF_A_TRUSTED_BOARD_BOOT=$(TF_A_TRUSTED_BOARD_BOOT)' 'COMPILE_NS_USER=$(COMPILE_NS_USER)' 'COMPILE_NS_KERNEL=$(COMPILE_NS_KERNEL)' 'COMPILE_S_USER=$(COMPILE_S_USER)' 'COMPILE_S_KERNEL=$(COMPILE_S_KERNEL)' 'TF_A_FLAGS=$(TF_A_FLAGS)' 'OPTEE_OS_COMMON_FLAGS=$(OPTEE_OS_COMMON_FLAGS)' 'QEMU_BASE_ARGS=$(QEMU_BASE_ARGS)'

# Same QEMU_BASE_ARGS as upstream; two UARTs are explicitly captured. No
# host share is exposed. `script` in README captures UART0/terminal output.
series-console:
	@test -n "$(SERIES_SECURE_LOG)" || { echo 'Set SERIES_SECURE_LOG to an absolute new file'; exit 1; }
	@test ! -e "$(SERIES_SECURE_LOG)" || { echo 'Refusing to overwrite secure log'; exit 1; }
	@test -f "$(ROOT)/out-br/images/rootfs.cpio.gz"
	ln -sf $(ROOT)/out-br/images/rootfs.cpio.gz $(BINARIES_PATH)/
	cd $(BINARIES_PATH) && $(QEMU_BIN) $(QEMU_BASE_ARGS) $(QEMU_SCMI_ARGS) -serial mon:stdio -serial file:$(SERIES_SECURE_LOG)
