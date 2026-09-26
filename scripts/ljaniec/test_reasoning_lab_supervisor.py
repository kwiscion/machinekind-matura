"""CPU-only mock checks: no real Ollama, HTTP, SSH, GPU or model calls."""
import copy
import hashlib
import io
import json
import os
from pathlib import Path
import signal
import sys
import subprocess
import time
import tempfile
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import reasoning_lab as lab
import reasoning_lab_supervisor as sup


class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.binary = self.root / "ollama"
        self.binary.write_bytes(b"synthetic executable")
        self.binary.chmod(0o700)
        self.models = self.root / "models"
        (self.models / "blobs").mkdir(parents=True)
        self.models.chmod(0o700)
        self.assets = {}
        for data in (b"synthetic weights", b"synthetic projector"):
            digest = hashlib.sha256(data).hexdigest()
            (self.models / "blobs" / ("sha256-" + digest)).write_bytes(data)
            self.assets[digest] = len(data)
        model = self.models / "manifests/registry.ollama.ai/library/gemma4/12b-it-q4_K_M"
        model.parent.mkdir(parents=True)
        model.write_text(json.dumps({"config": {"digest": "sha256:" + next(iter(self.assets)), "size": self.assets[next(iter(self.assets))]},
                                     "layers": [{"digest": "sha256:" + d, "size": n} for d, n in self.assets.items()]}))
        self.model_digest = sup.file_sha256(model)
        self.owner = self.root / "private"
        self.m = {"ollama_binary": str(self.binary), "models_dir": str(self.models),
                  "host": "test-host", "cuda_visible_devices": "0", "base_url": "http://127.0.0.1:11436", "run_id": "test-wave",
                  "deadline_epoch": 1000, "max_wall_seconds": 90, "timeout_seconds": 60,
                  "manifest_file_sha256": "manifest", "controller_sha256": "controller"}
        for obj, attr, value in ((lab, "ASSETS", self.assets), (lab, "DIGEST", self.model_digest),
                                 (lab, "PRIVATE_ROOT", self.owner), (sup, "OLLAMA_SHA256", sup.file_sha256(self.binary))):
            p = patch.object(obj, attr, value)
            p.start()
            self.addCleanup(p.stop)

    def test_all_local_pins_checked(self):
        self.assertEqual(sup.verify_pins(self.m)["models_dir"], self.models)
        first = self.models / "blobs" / ("sha256-" + next(iter(self.assets)))
        first.write_bytes(b"x" * first.stat().st_size)
        with self.assertRaisesRegex(ValueError, "blob pin"):
            sup.verify_pins(self.m)

    def test_binary_pin_missing_assets_manifest_and_permissions(self):
        with patch.object(sup, "OLLAMA_SHA256", "0" * 64), self.assertRaisesRegex(ValueError, "executable SHA"):
            sup.verify_pins(self.m)
        self.models.chmod(0o777)
        with self.assertRaisesRegex(ValueError, "not group/world writable"):
            sup.verify_pins(self.m)
        self.models.chmod(0o700)
        (self.models / "blobs" / ("sha256-" + next(iter(self.assets)))).unlink()
        with self.assertRaisesRegex(ValueError, "blob pin"):
            sup.verify_pins(self.m)

    def test_missing_and_relative_actual_paths_refused(self):
        for field in ("ollama_binary", "models_dir"):
            for value in (None, "", "relative"):
                with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                    sup.verify_pins({**self.m, field: value})

    def test_symlink_and_manifest_tamper_refused(self):
        alias = self.root / "alias"
        alias.symlink_to(self.binary)
        with self.assertRaisesRegex(ValueError, "symlink"):
            sup.verify_pins({**self.m, "ollama_binary": str(alias)})
        model = self.models / "manifests/registry.ollama.ai/library/gemma4/12b-it-q4_K_M"
        model.write_bytes(b"tampered")
        with self.assertRaisesRegex(ValueError, "manifest digest"):
            sup.verify_pins(self.m)

    def test_remaining_uses_wall_and_utc_independently(self):
        self.assertEqual(sup.remaining(self.m, 100, lambda: 98, lambda: 999), 1)
        for clock, utc in ((100, 900), (90, 1000)):
            with self.subTest(clock=clock), self.assertRaisesRegex(ValueError, "deadline"):
                sup.remaining(self.m, 100, lambda: clock, lambda: utc)

    def test_monitor_expiry_and_server_exit_and_controller_exit(self):
        server, controller = Mock(), Mock()
        server.poll.return_value = None
        controller.poll.return_value = None
        with self.assertRaisesRegex(ValueError, "deadline"):
            sup.monitor(server, controller, self.m, 100, clock=lambda: 100, utc=lambda: 900, pause=Mock())
        server.poll.return_value = 1
        with self.assertRaisesRegex(ValueError, "guardian/server exited"):
            sup.monitor(server, controller, self.m, 100, clock=lambda: 90, utc=lambda: 900, pause=Mock())
        server.poll.return_value = None
        controller.poll.return_value = 7
        self.assertEqual(sup.monitor(server, controller, self.m, 100, clock=lambda: 90, utc=lambda: 900, pause=Mock()), 7)

    def test_group_cleanup_kills_only_fresh_group_and_reaps(self):
        process = Mock(pid=246)
        identity = {"pid": 246, "pgid": 246, "start_ticks": 3}
        with patch.object(sup, "process_identity", return_value=identity), patch.object(sup.os, "killpg") as kill:
            sup.kill_owned_group(process, identity)
        kill.assert_called_once_with(246, signal.SIGKILL)
        process.wait.assert_called_once_with(timeout=5)
        with patch.object(sup, "process_identity", return_value={**identity, "start_ticks": 4}), patch.object(sup.os, "killpg") as kill:
            with self.assertRaisesRegex(ValueError, "PID was reused"):
                sup.kill_owned_group(process, identity)
        kill.assert_not_called()

    def test_cleanup_still_reaps_when_group_already_gone(self):
        process = Mock(pid=246)
        with patch.object(sup, "process_identity", side_effect=FileNotFoundError), patch.object(sup.os, "killpg", side_effect=ProcessLookupError):
            sup.kill_owned_group(process, {"pid": 246, "pgid": 246, "start_ticks": 3})
        process.wait.assert_called_once()

    def test_occupied_endpoint_refused_without_probe(self):
        sock = Mock()
        sock.__enter__ = Mock(return_value=sock)
        sock.__exit__ = Mock(return_value=False)
        sock.bind.side_effect = OSError("occupied")
        with patch.object(sup.socket, "socket", return_value=sock), self.assertRaises(OSError):
            sup.check_free_endpoint(self.m["base_url"])
        sock.bind.assert_called_once_with(("127.0.0.1", 11436))
        sock.connect.assert_not_called()

    def test_global_owner_lock_refuses_second_claim(self):
        from contextlib import ExitStack
        self.owner.mkdir()
        with ExitStack() as first, ExitStack() as second:
            sup.acquire_lock(self.owner / "lock", first)
            with self.assertRaises(BlockingIOError):
                sup.acquire_lock(self.owner / "lock", second)

    def test_supervisor_refuses_wrong_host_expiry_and_run_path_before_start(self):
        with patch.object(sup.time, "time", return_value=1000), patch.object(sup.subprocess, "Popen") as start:
            with self.assertRaisesRegex(ValueError, "deadline"):
                sup.supervise("manifest", "panel", self.owner / "run", self.m)
        start.assert_not_called()
        with patch.object(sup.time, "time", return_value=900), patch.object(sup.socket, "gethostname", return_value="other"), patch.object(sup.subprocess, "Popen") as start:
            with self.assertRaisesRegex(ValueError, "actual local"):
                sup.supervise("manifest", "panel", self.owner / "run", self.m)
        start.assert_not_called()

    def run_supervisor_mock(self, failure=None):
        guardian, controller = Mock(pid=245), Mock(pid=247)
        identities = {245: {"pid": 245, "pgid": 245, "session": 245, "ppid": os.getpid(), "start_ticks": 2},
                      246: {"pid": 246, "pgid": 246, "session": 246, "ppid": 245, "start_ticks": 3},
                      247: {"pid": 247, "pgid": 247, "session": 247, "ppid": os.getpid(), "start_ticks": 4}}
        guardian.stdout.readline.return_value = json.dumps(identities[246]).encode() + b"\n"
        with patch.object(sup.time, "time", return_value=900), patch.object(sup.socket, "gethostname", return_value="test-host"), \
             patch.object(sup, "check_free_endpoint"), patch.object(sup, "listener_owned", return_value=True), \
             patch.object(sup.select, "select", return_value=([guardian.stdout], [], [])), \
             patch.object(sup, "same_process", return_value=True), \
             patch.object(sup, "process_identity", side_effect=lambda pid: identities.get(pid, {"pid": pid})), \
             patch.object(sup.subprocess, "Popen", side_effect=[guardian, controller]) as start, \
             patch.object(sup, "monitor", side_effect=failure, return_value=0), patch.object(sup, "kill_owned_group") as cleanup, \
             patch.object(sup, "kill_server_group") as stop_server:
            if failure:
                with self.assertRaises(type(failure)):
                    sup.supervise("manifest", "panel", self.owner / "run", self.m)
            else:
                self.assertEqual(sup.supervise("manifest", "panel", self.owner / "run", self.m), 0)
        stop_server.assert_called_once_with(identities[246])
        guardian.wait.assert_called_once_with(timeout=5)
        self.assertEqual([c.args[0] for c in cleanup.call_args_list], [controller])
        self.assertEqual(start.call_count, 2)
        self.assertTrue(all(call.kwargs["start_new_session"] for call in start.call_args_list))
        self.assertEqual(start.call_args_list[0].args[0], [sys.executable, str(sup.HERE), "--guardian"])
        self.assertEqual(start.call_args_list[0].kwargs["env"]["OLLAMA_MODELS"], str(self.models))
        self.assertEqual(start.call_args_list[0].kwargs["env"]["OLLAMA_CONTEXT_LENGTH"], "32768")
        self.assertFalse((self.owner / "run").exists())

    def test_success_always_stops_server_and_controller_groups(self):
        self.run_supervisor_mock()

    def test_monitor_exception_always_stops_both_groups(self):
        self.run_supervisor_mock(ValueError("Supervisor deadline elapsed"))

    def test_missing_fd_and_plain_json_file_cannot_supply_proof(self):
        with patch.dict(os.environ, {}, clear=True), self.assertRaisesRegex(ValueError, "Protected supervisor"):
            sup.verify_parent_proof(self.m)
        proof = self.root / "fake-proof.json"
        proof.write_text('{"active":true}')
        with proof.open() as handle, patch.dict(os.environ, {sup.PROOF_ENV: str(handle.fileno())}), self.assertRaisesRegex(ValueError, "inherited pipe"):
            sup.verify_parent_proof(self.m)

    def test_guard_refuses_arbitrary_active_json_even_with_processes(self):
        proof = {"active": True, "guardian": {"pid": 245, "ppid": os.getppid()}, "parent": {"pid": os.getppid()}, "server": {"pid": 246, "pgid": 246, "session": 246, "ppid": 245}}
        with patch.object(sup, "same_process", return_value=True), self.assertRaisesRegex(ValueError, "lease lost"):
            sup.guard_parent_proof(proof, self.m)

    def test_parent_proof_accepts_python_B_relative_and_absolute_script(self):
        read_fd, write_fd = os.pipe()
        self.addCleanup(os.close, read_fd)
        self.addCleanup(os.close, write_fd)
        parent_pid = os.getppid()
        proof = {"parent": {"pid": parent_pid}, "guardian": {"pid": 241, "ppid": parent_pid},
                 "server": {"pid": 242, "pgid": 242, "session": 242, "ppid": 241},
                 "owner_lock_held": True, "manifest_sha256": "manifest", "controller_sha256": "controller",
                 "supervisor_sha256": "supervisor", "base_url": self.m["base_url"],
                 "deadline_epoch": self.m["deadline_epoch"], "max_wall_seconds": self.m["max_wall_seconds"],
                 "proof_fd": read_fd, "writer_fd": write_fd, "pipe_inode": os.fstat(read_fd).st_ino, "monotonic_end": 2000}
        for script in (str(sup.HERE), "scripts/ljaniec/reasoning_lab_supervisor.py"):
            with self.subTest(script=script), \
                 patch.object(sup, "same_process", return_value=True), \
                 patch.object(sup, "file_sha256", side_effect=lambda p: "controller" if p == sup.CONTROLLER else "supervisor"), \
                 patch.object(Path, "read_bytes", return_value=b"python3\0-B\0" + os.fsencode(script) + b"\0--manifest\0actual.json\0--execute\0"), \
                 patch.object(sup.os, "readlink", return_value=str(sup.HERE.parents[2])), \
                 patch.object(Path, "stat", return_value=os.fstat(write_fd)), \
                 patch.object(sup, "remaining", return_value=1):
                sup.guard_parent_proof(proof, self.m)
        for option in ("-c", "-m", "--unknown"):
            with self.subTest(option=option), self.assertRaisesRegex(ValueError, "reviewed foreground"):
                sup.parent_launch_script([b"python3", option.encode(), os.fsencode(sup.HERE), b"--execute"], parent_pid)

    def test_check_mode_never_starts_process_or_opens_socket(self):
        task = {"calls": 2}
        with patch.object(lab, "load_manifest", return_value=self.m), patch.object(lab, "load_panel", return_value=[task]), \
             patch.object(sup.subprocess, "Popen") as start, patch.object(sup.socket, "socket") as sock, \
             patch.object(sys, "stdout", io.StringIO()) as output:
            self.assertEqual(sup.main(["--manifest", "m", "--panel", "p"]), 0)
        self.assertIn('"http_requests": 0', output.getvalue())
        start.assert_not_called()
        sock.assert_not_called()

    def test_real_cpu_child_group_is_stopped_and_direct_child_reaped(self):
        script = "import subprocess,sys,time; p=subprocess.Popen([sys.executable,'-c','import time; time.sleep(30)']); print(p.pid,flush=True); time.sleep(30)"
        process = subprocess.Popen([sys.executable, "-c", script], stdout=subprocess.PIPE, text=True, start_new_session=True)
        identity = sup.process_identity(process.pid)
        child_pid = int(process.stdout.readline())
        try:
            self.assertEqual(sup.process_identity(child_pid)["pgid"], process.pid)
            sup.kill_owned_group(process, identity)
            self.assertIsNotNone(process.returncode)
            limit = time.monotonic() + 2
            while time.monotonic() < limit:
                try:
                    child = sup.process_identity(child_pid)
                except FileNotFoundError:
                    break
                if child["state"] in ("Z", "X"):
                    break
                time.sleep(0.01)
            else:
                self.fail("CPU child survived owned process group stop")
        finally:
            if process.poll() is None:
                sup.kill_owned_group(process, identity)
            process.stdout.close()

    def test_real_guardian_stops_and_reaps_server_after_foreground_sigkill(self):
        dummy = self.root / "dummy-server"
        dummy.write_text("#!" + sys.executable + "\nimport time\ntime.sleep(30)\n")
        dummy.chmod(0o700)
        log = self.root / "guardian.log"
        log.touch()
        wrapper = """
import json,os,subprocess,sys,time
sys.path.insert(0, sys.argv[1])
import reasoning_lab_supervisor as sup
parent=sup.process_identity(os.getpid())
g=subprocess.Popen([sys.executable,str(sup.HERE),'--guardian'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL)
spec={'parent':parent,'manifest':{'deadline_epoch':time.time()+10},'end':time.monotonic()+10,'binary':sys.argv[2],'env':dict(os.environ),'log':sys.argv[3]}
g.stdin.write(json.dumps(spec).encode()+b'\\n');g.stdin.flush()
server=json.loads(g.stdout.readline())
print(json.dumps({'guardian':g.pid,'server':server}),flush=True)
time.sleep(30)
"""
        parent = subprocess.Popen([sys.executable, "-c", wrapper, str(sup.HERE.parent), str(dummy), str(log)], stdout=subprocess.PIPE, text=True)
        data = json.loads(parent.stdout.readline())
        try:
            os.kill(parent.pid, signal.SIGKILL)
            parent.wait(timeout=2)
            deadline = time.monotonic() + 3
            while time.monotonic() < deadline:
                if not Path(f"/proc/{data['server']['pid']}").exists():
                    break
                time.sleep(0.02)
            else:
                self.fail("Independent guardian did not stop/reap fresh CPU server after supervisor SIGKILL")
        finally:
            if parent.poll() is None:
                parent.kill()
                parent.wait(timeout=2)
            sup.kill_server_group(data["server"])
            parent.stdout.close()

    def test_actual_manifest_fields_absent_block_check(self):
        incomplete = {**self.m, "models_dir": None}
        with patch.object(lab, "load_manifest", return_value=incomplete), patch.object(lab, "load_panel", return_value=[]), patch.object(sys, "stderr", io.StringIO()), patch.object(sup.subprocess, "Popen") as start:
            self.assertEqual(sup.main(["--manifest", "m", "--panel", "p"]), 2)
        start.assert_not_called()


if __name__ == "__main__":
    unittest.main()
