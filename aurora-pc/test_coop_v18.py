"""Protocol and compatibility safety checks for paired Aurora 1.7+1.8."""
import json
from pathlib import Path
import socket
import tempfile
import time
import unittest

import coop_v18 as coop


class LANProtocol(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.game=self.root/"game"
        self.game.mkdir()
        (self.game/"Stardew Valley.exe").write_bytes(b"fake")
        (self.game/"StardewModdingAPI.exe").write_bytes(b"fake")
        self.mod=self.game/"Mods"/"Fake Test"
        self.mod.mkdir(parents=True)
        (self.mod/"manifest.json").write_text(json.dumps({
            "UniqueID":"Example.Test", "Name":"Test",
            "Version":"1.2.3"}),encoding="utf8")

    def test_lan_probe_nonce_and_rfc1918(self):
        self.assertTrue(coop.local_address("192.168.1.1"))
        self.assertTrue(coop.local_address("10.2.3.4"))
        self.assertTrue(coop.local_address("172.16.2.3"))
        for ip in ("8.8.8.8","192.0.2.1","172.32.0.1","256.0.0.1"):
            self.assertFalse(coop.local_address(ip))
        nonce=b"abcdef9876543210"
        payload=coop.DISCOVER_PREFIX+nonce
        self.assertEqual(coop.reply_probe(payload,"192.168.1.7"),
                         coop.REPLY_PREFIX+nonce+b" 24643")
        self.assertIsNone(coop.reply_probe(payload,"8.8.8.8"))
        for item in (b"AURORA_DISCOVER_V2 bad", b"AURORA_DISCOVER_V2 "+"x".encode()*16,
                     b"AURORA_DISCOVER_V1 "+nonce):
            self.assertIsNone(coop.reply_probe(item,"192.168.1.7"))

    def test_compat_snapshot_versions_are_user_declared_not_attested(self):
        data=coop.compatibility_status(self.game,"Default","1.6.15","4.5.2")
        self.assertEqual(data["schema"],"aurora-coop-status/v2")
        self.assertEqual(data["game_version"],"1.6.15")
        self.assertEqual(data["smapi_version"],"4.5.2")
        self.assertIn("user-declared",data["version_source"])
        self.assertEqual(data["mods"],[{"id":"Example.Test","version":"1.2.3"}])
        self.assertNotIn("folder",str(data))
        self.assertNotIn(str(self.game),str(data))
        for bad in ("invalid version string","a"*80,"x/y"):
            with self.assertRaises(ValueError):
                coop.declared_version(bad)

    def test_network_server_udp_probe_and_tcp_payload(self):
        service=coop.CoopLANService(self.game,"Default","1.6.15","4.5.2",
                                    tcp_port=0,udp_port=0)
        try:
            service.start()
            tcpport=service._tcp.server_address[1]
            udpport=service._udp.getsockname()[1]
            nonce=b"0123456789abcdef"
            with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as udp:
                udp.settimeout(2)
                udp.sendto(coop.DISCOVER_PREFIX+nonce,("127.0.0.1",udpport))
                result,address=udp.recvfrom(128)
                self.assertEqual(result,coop.REPLY_PREFIX+nonce+b" 24643")
            with socket.create_connection(("127.0.0.1",tcpport),timeout=2) as client:
                client.settimeout(2)
                stream=client.makefile("rb")
                answer=json.loads(stream.readline(33000))
                stream.close()
            self.assertEqual(answer["mods"][0]["id"],"Example.Test")
            self.assertEqual(answer["game_version"],"1.6.15")
        finally:
            service.stop()

    def test_no_public_network_and_no_auto_game_join(self):
        with self.assertRaises(ValueError):
            coop.compatibility_status(self.game,"Default","../bad","4.5.2")
        self.assertEqual(coop.UDP_PORT,24644)
        self.assertEqual(coop.TCP_PORT,24643)


if __name__ == "__main__":
    unittest.main()
