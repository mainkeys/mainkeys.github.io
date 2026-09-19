#!/usr/bin/env python3
"""教学状态模型；不是生产安全代码，也不是 CA/TA、RPMB 或 AVB 实测。
运行：python3 authorization-model.py（Python 3.10 以上，无第三方依赖）。

身份、镜像和 nonce 均为合成数据；假定令牌已通过外部真实性验证。
Authorization 表示一个目标槽关联的逻辑状态。accepted/candidate 保存完整
Token，用于教学中的软件及事务绑定；这是模型额外约束，不等于真实固件
只存 nonce 的布局，也不描述任何实际字段或偏移。
submit 登记候选授权；can_boot 只检查准入，不改变状态。
commit_success 假定外部可信的启动成功判定已完成，再提交授权状态；
此入口不接收普通世界自报的 success 布尔值，也不实现成功信号的认证。
新授权匹配 pending nonce，当前 accepted 授权可以继续启动。
这里没有签名、可信摘要来源、并发、掉电恢复或不可回滚存储。
串行重复提交的幂等检查不证明掉电或并发安全。
rotations 只给符号 nonce 命名，会随快照回退，不是可信单调计数器。
AVB 部分仅模拟一个 rollback-index location 的整数比较与 floor 更新。
"""
from copy import deepcopy
from dataclasses import dataclass
from hashlib import sha256


@dataclass(frozen=True)
class Token:
    device: str
    digest: str
    nonce: str


@dataclass
class Authorization:
    device: str
    pending: str = "NONCE-1"
    candidate: Token | None = None
    accepted: Token | None = None
    rotations: int = 0

    def matches_target(self, token, image_digest):
        return token.device == self.device and token.digest == image_digest

    def submit(self, token, image_digest):
        if not self.matches_target(token, image_digest):
            return "rejected"
        if token == self.accepted:
            return "accepted"
        if token.nonce != self.pending:
            return "rejected"
        if self.candidate is not None and self.candidate != token:
            return "rejected"
        self.candidate = token
        return "pending"

    def can_boot(self, token, image_digest):
        """只检查授权准入；不代表镜像已实际启动或启动成功。"""
        if not self.matches_target(token, image_digest):
            return False
        if token == self.accepted:
            return True
        return token == self.candidate and token.nonce == self.pending

    def commit_success(self, token, image_digest):
        """仅在外部可信成功判定完成后调用；不在这里验证成功信号。"""
        if not self.can_boot(token, image_digest):
            return False
        if token == self.accepted:
            return True
        self.accepted, self.candidate = token, None
        self.rotations += 1
        self.pending = f"NONCE-{self.rotations + 1}"
        return True


def avb_allows(image_index, floor):
    # Reading/verifying an image does not itself commit a higher floor.
    return image_index >= floor


def check(number, description, condition):
    if not condition:
        raise AssertionError(f"case {number}: {description}")
    print(f"PASS {number:02d}: {description}")


def main():
    image_a = sha256(b"synthetic-image-A").hexdigest()
    image_b = sha256(b"synthetic-image-B").hexdigest()
    state = Authorization("DEMO-DEVICE-A")
    token_a = Token(state.device, image_a, "NONCE-1")
    original = deepcopy(state)

    wrong_device = Token("DEMO-DEVICE-B", image_a, state.pending)
    check(1, "wrong device rejected", state.submit(wrong_device, image_a) == "rejected"
          and not state.can_boot(wrong_device, image_a)
          and not state.commit_success(wrong_device, image_a) and state == original)
    check(2, "wrong image digest rejected", state.submit(token_a, image_b) == "rejected"
          and not state.can_boot(token_a, image_b)
          and not state.commit_success(token_a, image_b) and state == original)
    wrong_nonce = Token(state.device, image_a, "NONCE-UNRELATED")
    check(3, "wrong pending nonce rejected", state.submit(wrong_nonce, image_a) == "rejected"
          and not state.can_boot(wrong_nonce, image_a)
          and not state.commit_success(wrong_nonce, image_a) and state == original)

    submitted = state.submit(token_a, image_a)
    before_boot = deepcopy(state)
    check(4, "matching and repeated submission stay pending", submitted == "pending"
          and state.submit(token_a, image_a) == "pending" and state == before_boot
          and state.accepted is None and state.rotations == 0)
    check(5, "trial-boot admission is read-only and does not rotate nonce",
          state.can_boot(token_a, image_a) and state.can_boot(token_a, image_a)
          and state == before_boot and state.pending == "NONCE-1")
    # For these calls, assume the trusted success decision was made externally.
    committed = state.commit_success(token_a, image_a)
    after_success = deepcopy(state)
    check(6, "success commit rotates once; repeated commit, reboot and submit are idempotent",
          committed and state.accepted == token_a and state.pending == "NONCE-2"
          and state.rotations == 1 and state.commit_success(token_a, image_a)
          and state.can_boot(token_a, image_a)
          and state.submit(token_a, image_a) == "accepted" and state == after_success)

    token_b = Token(state.device, image_b, state.pending)
    check(7, "next authorization replaces accepted token only on success commit",
          state.submit(token_b, image_b) == "pending" and state.can_boot(token_b, image_b)
          and state.accepted == token_a and state.pending == "NONCE-2"
          and state.commit_success(token_b, image_b)
          and state.accepted == token_b and state.pending == "NONCE-3")
    current = deepcopy(state)
    check(8, "old token replay rejected in current state",
          state.submit(token_a, image_a) == "rejected"
          and not state.can_boot(token_a, image_a)
          and not state.commit_success(token_a, image_a) and state == current)

    restored = deepcopy(before_boot)
    check(9, "restoring trusted-state snapshot makes old token acceptable again",
          restored.submit(token_a, image_a) == "pending"
          and restored.can_boot(token_a, image_a) and restored == before_boot)

    floor = 7
    check(10, "AVB rejects lower index, allows repeated equal-index boots",
          not avb_allows(6, floor) and all(avb_allows(7, floor) for _ in range(3)))
    check(11, "higher image index is allowed without automatically raising floor",
          avb_allows(8, floor) and floor == 7)
    old_slot_index, new_slot_index = 7, 8
    trial_boot_succeeded = False  # Synthetic failed trial, not a real boot.
    premature_floor = max(floor, new_slot_index)
    deferred_floor = max(floor, new_slot_index) if trial_boot_succeeded else floor
    check(12, "failed A/B trial: premature floor blocks old slot; deferred floor allows it",
          not avb_allows(old_slot_index, premature_floor)
          and avb_allows(old_slot_index, deferred_floor))

    # Exercise the nonce policy alone on a copy, assuming its trusted-success
    # prerequisite. In a combined boot flow, AVB rejection prevents this commit.
    nonce_only = deepcopy(current)  # image_b is already accepted, pending=N3.
    reissued_for_a = Token(nonce_only.device, image_a, nonce_only.pending)
    independent_floor = 8
    check(13, "fresh authorization for old software passes nonce policy; AVB still rejects index 7",
          reissued_for_a != token_a and nonce_only.submit(reissued_for_a, image_a) == "pending"
          and nonce_only.can_boot(reissued_for_a, image_a)
          and nonce_only.commit_success(reissued_for_a, image_a)
          and nonce_only.accepted == reissued_for_a
          and not avb_allows(7, independent_floor) and state == current)
    print("PASS: 13 model scenarios; no hardware, CA/TA, RPMB or AVB test performed.")


if __name__ == "__main__":
    main()
