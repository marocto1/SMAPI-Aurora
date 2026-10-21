import json
import socket
import tempfile
import unittest
from pathlib import Path

import coop_v20 as coop


class RoomPreviewTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.game=Path(self.temp.name)
        (self.game/"Stardew Valley.exe").write_bytes(b"x")
        (self.game/"StardewModdingAPI.exe").write_bytes(b"x")

    def test_invitation_parsing_and_rfc6598_overlay(self):
        token="a"*32
        for ip in ("192.168.1.2","10.2.3.4","100.88.4.9"):
            self.assertEqual(coop.parse_invite(coop.make_invite(ip,token)),(ip,token))
            self.assertTrue(coop.local_address(ip))
        for ip in ("100.100.100.100","8.8.8.8","100.128.1.2","192.0.2.1"):
            # 100.100.100.100 is reserved and must not be a room invitation target
            with self.assertRaises(ValueError):
                coop.make_invite(ip,token)
        for candidate in ("AURORA2|192.168.0.2|short",
                          "AURORA2|8.8.8.8|"+"a"*32,
                          "AURORA1|192.168.0.2|"+"a"*32):
            with self.assertRaises(ValueError):
                coop.parse_invite(candidate)

    def test_token_is_required_for_receiving_profile_metadata(self):
        service=coop.CoopLANService(self.game,tcp_port=0,udp_port=0)
        try:
            service.start()
            port=service._tcp.server_address[1]
            correct=service.room_token
            self.assertEqual(len(correct),32)
            def query(token):
                with socket.create_connection(("127.0.0.1",port),timeout=2) as conn:
                    conn.settimeout(3)
                    conn.sendall(("AURORA_ROOM_V1 "+token+"\n").encode())
                    return conn.recv(32768)
            self.assertEqual(query("0"*32),b"")
            data=json.loads(query(correct))
            self.assertEqual(data["schema"],coop.SCHEMA)
            self.assertEqual(data["launcher"],"Aurora SMAPI PC")
            self.assertNotIn(correct,str(data))
        finally:
            service.stop()

    def test_invalid_udp_probe_and_nonpublic_only(self):
        nonce=b"1234567890abcdef"
        self.assertIsNone(coop.reply_probe(coop.DISCOVER_PREFIX+nonce,"8.8.8.8"))
        self.assertEqual(coop.reply_probe(coop.DISCOVER_PREFIX+nonce,"192.168.1.3"),
                         coop.REPLY_PREFIX+nonce+b" 24643")


if __name__ == "__main__":
    unittest.main()
