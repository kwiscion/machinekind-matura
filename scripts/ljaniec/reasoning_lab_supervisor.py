"""Linux owned Ollama supervisor. Check mode hashes local files; never sends HTTP.

Execution requires a dedicated models_dir, actual local hostname, supplied rate,
and explicit deadline. It starts fresh session leaders and kills only those
owned groups on completion, interruption, server failure or deadline. Run this
as the foreground job; no existing daemon is adopted or stopped.
"""
from __future__ import annotations

import argparse
import ctypes
from contextlib import ExitStack
import fcntl
import hashlib
import ipaddress
import json
import os
from pathlib import Path
import select
import signal
import socket
import stat
import subprocess
import sys
import time
import urllib.parse

HERE = Path(__file__).resolve()
CONTROLLER = HERE.with_name("reasoning_lab.py")
OLLAMA_SHA256 = "ad9c53441752620a2314a65a798a888d98df3636c8815ca044de591f82892ff4"
PROOF_ENV = "REASONING_LAB_SUPERVISOR_FD"
POLL_SECONDS = 0.05
CLEANUP_MARGIN_SECONDS = 2


def file_sha256(path, guard=lambda: None):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        while block := handle.read(4 * 1024 * 1024):
            guard()
            digest.update(block)
    return digest.hexdigest()


def remaining(manifest, end, clock=None, utc=None):
    clock = time.monotonic if clock is None else clock
    utc = time.time if utc is None else utc
    left = min(end - clock(), manifest["deadline_epoch"] - utc())
    if left <= 0:
        raise ValueError("Supervisor deadline elapsed")
    return left


def verify_pins(manifest, guard=lambda: None):
    import reasoning_lab as lab
    paths = {}
    for field in ("ollama_binary", "models_dir"):
        value = manifest.get(field)
        if not isinstance(value, str) or not value.strip() or not Path(value).is_absolute():
            raise ValueError(f"Actual absolute {field} required")
        path = Path(value)
        if path.is_symlink():
            raise ValueError(f"{field} must not be a symlink")
        paths[field] = path.resolve(strict=True)
    binary, models = paths["ollama_binary"], paths["models_dir"]
    if not binary.is_file() or not os.access(binary, os.X_OK):
        raise ValueError("Pinned Ollama executable required")
    if not models.is_dir() or models.stat().st_uid != os.getuid() or models.stat().st_mode & 0o022:
        raise ValueError("Dedicated models_dir must be owned by current user and not group/world writable")
    if file_sha256(binary, guard) != OLLAMA_SHA256:
        raise ValueError("Ollama executable SHA256 differs from pinned build")
    for digest, size in lab.ASSETS.items():
        blob = models / "blobs" / ("sha256-" + digest)
        if blob.is_symlink() or not blob.is_file() or blob.stat().st_size != size or file_sha256(blob, guard) != digest:
            raise ValueError("Model/projector local blob pin mismatch")
    model_manifest = models / "manifests/registry.ollama.ai/library/gemma4/12b-it-q4_K_M"
    if model_manifest.is_symlink() or file_sha256(model_manifest, guard) != lab.DIGEST:
        raise ValueError("Local Ollama model manifest digest mismatch")
    native = json.loads(model_manifest.read_text())
    references = [native.get("config"), *native.get("layers", [])]
    if not references or not all(isinstance(r, dict) for r in references):
        raise ValueError("Native manifest config/layers required")
    for reference in references:
        digest = reference.get("digest", "")
        size = reference.get("size")
        if not isinstance(digest, str) or not __import__("re").fullmatch(r"sha256:[0-9a-f]{64}", digest) or type(size) is not int or size < 0:
            raise ValueError("Native manifest asset reference invalid")
        blob = models / "blobs" / digest.replace(":", "-", 1)
        if blob.is_symlink() or not blob.is_file() or blob.stat().st_size != size or file_sha256(blob, guard) != digest[7:]:
            raise ValueError("Native manifest config/layer pin mismatch")
    return paths


def process_identity(pid):
    """/proc stat fields exclude comm, which may contain spaces or parentheses."""
    data = Path(f"/proc/{pid}/stat").read_text()
    fields = data[data.rfind(")") + 2:].split()
    return {"pid": pid, "state": fields[0], "ppid": int(fields[1]),
            "pgid": int(fields[2]), "session": int(fields[3]), "start_ticks": int(fields[19])}


def same_process(expected):
    try:
        actual = process_identity(expected["pid"])
        return actual["state"] not in ("Z", "X") and all(actual[k] == expected[k] for k in ("pid", "ppid", "pgid", "session", "start_ticks"))
    except (OSError, ValueError, KeyError):
        return False


def verify_parent_proof(manifest):
    """Require inherited FIFO and living, identified supervisor+owned server.

    A JSON file or a manifest active=true flag is never accepted as a lease.
    This protects operational misuse, not a malicious process running as the
    same Unix user (which can modify this code and its process environment).
    """
    try:
        fd = int(os.environ[PROOF_ENV])
        if not stat.S_ISFIFO(os.fstat(fd).st_mode):
            raise ValueError("Supervisor proof FD must be an inherited pipe")
        if not select.select([fd], [], [], 0)[0]:
            raise ValueError("Supervisor proof unavailable")
        data = os.read(fd, 32769)
        if len(data) > 32768 or not data.endswith(b"\n"):
            raise ValueError("Malformed supervisor proof")
        proof = json.loads(data)
        proof["proof_fd"] = fd
        proof["pipe_inode"] = os.fstat(fd).st_ino
        guard_parent_proof(proof, manifest)
        return proof
    except (KeyError, OSError, TypeError, json.JSONDecodeError) as exc:
        raise ValueError("Protected supervisor parent proof required") from exc


def parent_launch_script(cmdline, parent_pid):
    """Resolve the direct Python script after harmless interpreter switches.

    Reject -c/-m wrappers: execution must enter this reviewed script directly.
    """
    arguments = [os.fsdecode(arg) for arg in cmdline if arg]
    index = 1
    allowed = {"-B", "-I", "-u", "-E", "-s", "-S", "-O", "-OO", "-q"}
    while index < len(arguments) and arguments[index] in allowed:
        index += 1
    if index >= len(arguments) or arguments[index].startswith("-"):
        raise ValueError("Parent is not the reviewed foreground supervisor")
    launch_path = Path(arguments[index])
    if not launch_path.is_absolute():
        launch_path = Path(os.readlink(f"/proc/{parent_pid}/cwd")) / launch_path
    return launch_path.resolve()


def guard_parent_proof(proof, manifest):
    parent, server, guardian = proof["parent"], proof["server"], proof["guardian"]
    if (parent["pid"] != os.getppid() or not same_process(parent) or not same_process(server)
            or not same_process(guardian) or guardian["ppid"] != parent["pid"]
            or server["ppid"] != guardian["pid"] or server["pid"] != server["pgid"]
            or server["session"] != server["pid"] or proof.get("owner_lock_held") is not True):
        raise ValueError("Supervisor/server process lease lost")
    expected = {"manifest_sha256": manifest["manifest_file_sha256"], "controller_sha256": manifest["controller_sha256"],
                "base_url": manifest["base_url"], "deadline_epoch": manifest["deadline_epoch"],
                "max_wall_seconds": manifest["max_wall_seconds"], "supervisor_sha256": file_sha256(HERE)}
    if any(proof.get(k) != v for k, v in expected.items()):
        raise ValueError("Supervisor proof does not bind current manifest/controller/deadline")
    cmdline = Path(f"/proc/{parent['pid']}/cmdline").read_bytes().split(b"\0")
    if len(cmdline) < 3 or b"--execute" not in cmdline:
        raise ValueError("Parent is not the reviewed foreground supervisor")
    if parent_launch_script(cmdline, parent["pid"]) != HERE:
        raise ValueError("Parent is not the reviewed foreground supervisor")
    if file_sha256(CONTROLLER) != manifest["controller_sha256"]:
        raise ValueError("Controller changed during owned run")
    parent_pipe = Path(f"/proc/{parent['pid']}/fd/{proof['writer_fd']}")
    if (os.fstat(proof["proof_fd"]).st_ino != proof["pipe_inode"]
            or parent_pipe.stat().st_ino != proof["pipe_inode"]):
        raise ValueError("Supervisor no longer owns proof pipe")
    remaining(manifest, proof["monotonic_end"])


def acquire_lock(path, stack):
    flags = os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW
    fd = os.open(path, flags, 0o600)
    handle = stack.enter_context(os.fdopen(fd, "a"))
    fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    return handle


def check_free_endpoint(base_url):
    parsed = urllib.parse.urlsplit(base_url)
    family = socket.AF_INET6 if ":" in parsed.hostname else socket.AF_INET
    # Bind only, never probe/adopt a pre-existing HTTP service.
    with socket.socket(family, socket.SOCK_STREAM) as sock:
        sock.bind((parsed.hostname, parsed.port or 80))


def listener_owned(pid, base_url):
    parsed = urllib.parse.urlsplit(base_url)
    address = ipaddress.ip_address(parsed.hostname)
    inodes = set()
    for fd in Path(f"/proc/{pid}/fd").iterdir():
        try:
            target = os.readlink(fd)
            if target.startswith("socket:["):
                inodes.add(target[8:-1])
        except OSError:
            continue
    table = "/proc/net/tcp6" if address.version == 6 else "/proc/net/tcp"
    for row in Path(table).read_text().splitlines()[1:]:
        fields = row.split()
        raw, port = fields[1].split(":")
        packed = bytes.fromhex(raw)
        if sys.byteorder == "little":
            packed = b"".join(packed[i:i + 4][::-1] for i in range(0, len(packed), 4))
        if fields[3] == "0A" and fields[9] in inodes and int(port, 16) == (parsed.port or 80) and ipaddress.ip_address(packed) == address:
            return True
    return False


def kill_owned_group(process, identity):
    if process is None:
        return
    # Never re-resolve an arbitrary user-supplied PID. Only fresh Popen groups.
    if identity and identity["pid"] == process.pid and identity["pgid"] == process.pid:
        try:
            current = process_identity(process.pid)
            if current["start_ticks"] != identity["start_ticks"]:
                raise ValueError("Owned process PID was reused; refusing kill")
        except FileNotFoundError:
            current = None
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    else:
        # Startup failed before identity capture: the unreaped direct child
        # cannot have its PID reused. start_new_session=True creates its group.
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    process.wait(timeout=5)


def kill_server_group(identity):
    # Pinned Ollama v0.34.4 llm/llm_linux.go uses empty SysProcAttr;
    # llama-server inherits this group/session. The CPU regression checks
    # real inherited descendants, not only mock killpg calls.
    # Fresh child identity from guardian, never an operator-supplied PID.
    try:
        current = process_identity(identity["pid"])
        if current["start_ticks"] != identity["start_ticks"]:
            raise ValueError("Owned server PID reused")
    except FileNotFoundError:
        pass
    try:
        os.killpg(identity["pgid"], signal.SIGKILL)
    except ProcessLookupError:
        pass


def parent_death_kill(expected_parent):
    """Linux startup bridge before the independent guardian is ready."""
    if ctypes.CDLL(None, use_errno=True).prctl(1, signal.SIGKILL, 0, 0, 0) != 0:
        raise OSError(ctypes.get_errno(), "prctl(PR_SET_PDEATHSIG) failed")
    if os.getppid() != expected_parent:
        os.kill(os.getpid(), signal.SIGKILL)


def guardian_worker():
    """Own/reap the server independently if foreground supervisor disappears."""
    spec = json.loads(sys.stdin.buffer.readline(32769))
    parent = spec["parent"]
    if parent["pid"] != os.getppid() or not same_process(parent):
        raise ValueError("Guardian requires living launch parent")
    server = identity = None
    try:
        remaining(spec["manifest"], spec["end"])
        with Path(spec["log"]).open("a") as log:
            guardian_pid = os.getpid()
            server = subprocess.Popen([spec["binary"], "serve"], env=spec["env"], stdin=subprocess.DEVNULL,
                                      stdout=log, stderr=log, start_new_session=True, preexec_fn=lambda: parent_death_kill(guardian_pid))
            identity = process_identity(server.pid)
            sys.stdout.write(json.dumps(identity) + "\n")
            sys.stdout.flush()
            while True:
                remaining(spec["manifest"], spec["end"])
                if not same_process(parent) or os.getppid() != parent["pid"]:
                    raise ValueError("Supervisor parent disappeared")
                if server.poll() is not None:
                    return server.returncode
                time.sleep(POLL_SECONDS)
    finally:
        kill_owned_group(server, identity)


def monitor(guardian, controller, manifest, end, clock=time.monotonic, utc=time.time, pause=time.sleep):
    while True:
        remaining(manifest, end, clock, utc)
        if guardian.poll() is not None:
            raise ValueError("Owned Ollama guardian/server exited during wave")
        code = controller.poll()
        if code is not None:
            return code
        pause(min(POLL_SECONDS, remaining(manifest, end, clock, utc)))


def supervise(manifest_path, panel_path, run_dir, manifest):
    import reasoning_lab as lab
    end = time.monotonic() + manifest["max_wall_seconds"] - CLEANUP_MARGIN_SECONDS
    bounded = {**manifest, "deadline_epoch": manifest["deadline_epoch"] - CLEANUP_MARGIN_SECONDS}
    guard = lambda: remaining(bounded, end)
    guard()
    if manifest["host"] != socket.gethostname():
        raise ValueError("Manifest host must equal actual local socket.gethostname()")
    cuda = manifest.get("cuda_visible_devices")
    if not isinstance(cuda, str) or not __import__("re").fullmatch(r"[0-9]+(?:,[0-9]+)*", cuda):
        raise ValueError("Actual cuda_visible_devices required")
    run_dir = Path(run_dir).resolve()
    owner_root = lab.PRIVATE_ROOT.resolve()
    if not run_dir.is_relative_to(owner_root) or run_dir == owner_root or run_dir.exists():
        raise ValueError("Require new run directory under agentsLog/ljaniec/private")
    guardian = controller = guardian_id = controller_id = server_id = None
    read_fd = write_fd = None
    with ExitStack() as stack:
        owner_root.mkdir(parents=True, mode=0o700, exist_ok=True)
        acquire_lock(owner_root / "reasoning-lab-owner.lock", stack)
        paths = verify_pins(manifest, guard)
        acquire_lock(paths["models_dir"] / "reasoning-lab-runtime.lock", stack)
        check_free_endpoint(manifest["base_url"])
        # Only runtime necessities: inherited LLAMA_ARG/GGML/CUDA/OLLAMA settings
        # and unrelated credentials cannot alter this dedicated worker.
        env = {k: v for k, v in os.environ.items() if k in {"PATH", "HOME", "USER", "LOGNAME", "LANG", "LC_ALL", "LD_LIBRARY_PATH"}}
        env.update(OLLAMA_HOST=urllib.parse.urlsplit(manifest["base_url"]).netloc,
                   OLLAMA_MODELS=str(paths["models_dir"]), OLLAMA_NO_CLOUD="1",
                   OLLAMA_CONTEXT_LENGTH="32768", OLLAMA_MAX_LOADED_MODELS="1", OLLAMA_NUM_PARALLEL="1",
                   CUDA_VISIBLE_DEVICES=cuda)
        log_path = owner_root / ("reasoning-lab-supervisor-" + hashlib.sha256(manifest["run_id"].encode()).hexdigest()[:16] + ".log")
        log = stack.enter_context(log_path.open("x"))
        os.fchmod(log.fileno(), 0o600)
        old_handlers = {}
        def interrupted(signum, frame):
            raise InterruptedError(f"Supervisor interrupted by signal {signum}")
        for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
            old_handlers[sig] = signal.signal(sig, interrupted)
        try:
            guard()
            parent_id = process_identity(os.getpid())
            guardian = subprocess.Popen([sys.executable, str(HERE), "--guardian"], env=env,
                        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=log, start_new_session=True)
            guardian_id = process_identity(guardian.pid)
            spec = {"parent": parent_id, "manifest": bounded, "end": end, "binary": str(paths["ollama_binary"]),
                    "env": env, "log": str(log_path)}
            guardian.stdin.write(json.dumps(spec).encode() + b"\n")
            guardian.stdin.flush()
            startup_end = min(end, time.monotonic() + manifest["timeout_seconds"])
            while not select.select([guardian.stdout], [], [], min(POLL_SECONDS, remaining(bounded, startup_end)))[0]:
                if guardian.poll() is not None:
                    raise ValueError("Guardian failed before owned server identity")
            data = guardian.stdout.readline(32769)
            if not data.endswith(b"\n") or len(data) > 32768:
                raise ValueError("Invalid owned server identity")
            server_id = json.loads(data)
            if not same_process(server_id) or server_id["ppid"] != guardian.pid or server_id["pgid"] != server_id["pid"]:
                raise ValueError("Guardian did not create fresh owned server")
            while not listener_owned(server_id["pid"], manifest["base_url"]):
                remaining(bounded, startup_end)
                if guardian.poll() is not None:
                    raise ValueError("Fresh owned server failed before listening")
                time.sleep(POLL_SECONDS)
            read_fd, write_fd = os.pipe()
            proof = {"parent": parent_id, "guardian": guardian_id, "server": server_id, "owner_lock_held": True,
                     "writer_fd": write_fd, "monotonic_end": end, "base_url": manifest["base_url"],
                     "manifest_sha256": manifest["manifest_file_sha256"], "controller_sha256": manifest["controller_sha256"],
                     "supervisor_sha256": file_sha256(HERE), "deadline_epoch": manifest["deadline_epoch"],
                     "max_wall_seconds": manifest["max_wall_seconds"]}
            os.write(write_fd, json.dumps(proof).encode() + b"\n")
            env[PROOF_ENV] = str(read_fd)
            guard()
            controller = subprocess.Popen([sys.executable, str(CONTROLLER), "--manifest", str(Path(manifest_path).resolve()),
                        "--panel", str(Path(panel_path).resolve()), "--run-dir", str(run_dir), "--execute"],
                        env=env, pass_fds=(read_fd,), start_new_session=True, preexec_fn=lambda: parent_death_kill(parent_id["pid"]))
            controller_id = process_identity(controller.pid)
            return monitor(guardian, controller, bounded, end)
        finally:
            for sig in old_handlers:
                signal.signal(sig, signal.SIG_IGN)
            try:
                if server_id:
                    kill_server_group(server_id)
            finally:
                try:
                    # Guardian owns the server Popen and reaps it before exit.
                    if guardian:
                        try:
                            guardian.wait(timeout=5)
                        except subprocess.TimeoutExpired:
                            kill_owned_group(guardian, guardian_id)
                finally:
                    try:
                        kill_owned_group(controller, controller_id)
                    finally:
                        for fd in (read_fd, write_fd):
                            if fd is not None:
                                os.close(fd)
                        if guardian:
                            guardian.stdin.close()
                            guardian.stdout.close()
                        for sig, handler in old_handlers.items():
                            signal.signal(sig, handler)


def main(argv=None):
    import reasoning_lab as lab
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--panel", required=True, type=Path)
    parser.add_argument("--run-dir", type=Path)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args(argv)
    try:
        manifest = lab.load_manifest(args.manifest)
        tasks = lab.load_panel(args.panel, manifest)
        if not args.execute:
            verify_pins(manifest)
            print(json.dumps({"mode": "check", "planned_calls": sum(t["calls"] for t in tasks),
                              "http_requests": 0, "runtime_started": False, "local_pins_verified": True}))
            return 0
        if args.run_dir is None:
            raise ValueError("--execute requires --run-dir")
        return supervise(args.manifest, args.panel, args.run_dir, manifest)
    except (ValueError, OSError, subprocess.SubprocessError) as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    if sys.argv[1:] == ["--guardian"]:
        raise SystemExit(guardian_worker())
    raise SystemExit(main())
