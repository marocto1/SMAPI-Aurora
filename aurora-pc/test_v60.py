"""Aurora 6.0 PC: safe host-port diagnostic, not multiplayer verification."""
import subprocess
import unittest
from types import SimpleNamespace
import host_probe_v60 as probe


class GameHostProbeTests(unittest.TestCase):
    def test_windows_local_udp_listener_is_not_gameplay_verification(self):
        calls=[]
        def run(cmd,**kwargs):
            calls.append((cmd,kwargs))
            return SimpleNamespace(returncode=0,stdout="1\\n")
        result=probe.inspect_local_game_udp(platform="win32",which=lambda _: "pwsh.exe",runner=run)
        self.assertEqual(result["status"],"present")
        self.assertTrue(result["local_udp_listener_checked"])
        self.assertFalse(result["gameplay_verified"])
        self.assertIn("Get-NetUDPEndpoint",calls[0][0][-1])
        self.assertNotIn("Set-NetFirewallRule",str(calls))
        absent=probe.inspect_local_game_udp(platform="win32",which=lambda _: "pwsh.exe",
            runner=lambda *_a,**_k:SimpleNamespace(returncode=0,stdout="0"))
        self.assertEqual(absent["status"],"absent")
        self.assertFalse(absent["gameplay_verified"])

    def test_no_powershell_and_bad_output_fail_closed(self):
        self.assertEqual(probe.inspect_local_game_udp(platform="linux")["status"],"unsupported")
        self.assertEqual(probe.inspect_local_game_udp(platform="win32",which=lambda _:None)["status"],"unknown")
        bad=probe.inspect_local_game_udp(platform="win32",which=lambda _:"pwsh",
            runner=lambda *_a,**_k:SimpleNamespace(returncode=1,stdout="bad"))
        self.assertEqual(bad["status"],"unknown")
        timeout=probe.inspect_local_game_udp(platform="win32",which=lambda _:"pwsh",
            runner=lambda *_a,**_k:(_ for _ in ()).throw(subprocess.TimeoutExpired("pwsh",5)))
        self.assertEqual(timeout["status"],"unknown")


if __name__=="__main__":unittest.main()
