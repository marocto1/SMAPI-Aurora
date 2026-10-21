"""Local-only tests: private catalog, one-time pairing and expiring R2 links."""
import importlib.util
import json
import os
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

path=Path(__file__).with_name("app.py")
spec=importlib.util.spec_from_file_location("aurora_service",path)
app=importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)


class VersionServerTests(unittest.TestCase):
    def setUp(self):
        self.vars={
          "AURORA_ADMIN_TOKEN":"a"*48,
          "AURORA_SESSION_SECRET":"b"*64,
          "AURORA_R2_ACCOUNT_ID":"d0ab9fdebeadcc640b3fc0324da411b3",
          "AURORA_R2_BUCKET":"aurora-downloads",
          "AURORA_R2_ACCESS_KEY_ID":"ACCESSKEYTEST123",
          "AURORA_R2_SECRET_ACCESS_KEY":"secret-key-for-test-only-"+"x"*40,
          "AURORA_PRIVATE_CATALOG_JSON":json.dumps([{
              "id":"sdv-1.6.15.3-b245","version":"1.6.15.3.build.245",
              "object_key":"Stardew Valley_v1.6.15.3.build.245.apks",
              "sha256":"f"*64,"size":299_300_000,
              "rights":"owner-private-backup"}])
        }
        self.env=patch.dict(os.environ,self.vars)
        self.env.start()
        self.assertTrue(app.configured())
        self.http=ThreadingHTTPServer(("127.0.0.1",0),app.Handler)
        self.port=self.http.server_address[1]
        self.thread=threading.Thread(target=self.http.serve_forever,daemon=True)
        self.thread.start()

    def tearDown(self):
        self.http.shutdown();self.http.server_close()
        self.thread.join(timeout=2)
        self.env.stop()
        with app.LOCK:app.PAIRINGS.clear()

    def request(self,path,method="GET",bearer=None,data=None):
        headers={}
        if bearer is not None:headers["Authorization"]="Bearer "+bearer
        if data is not None:headers["Content-Type"]="application/json"
        req=urllib.request.Request(f"http://127.0.0.1:{self.port}"+path,
            method=method,headers=headers,
            data=None if data is None else json.dumps(data).encode())
        try:
            with urllib.request.urlopen(req,timeout=4) as r:
                return r.status,json.load(r)
        except urllib.error.HTTPError as e:
            return e.code,json.load(e)

    def test_no_public_game_feed(self):
        self.assertEqual(self.request("/health")[1]["ready"],True)
        self.assertEqual(self.request("/v1/versions")[0],401)
        self.assertEqual(self.request("/v1/download?id=sdv-1.6.15.3-b245")[0],401)

    def test_pair_once_then_download_presigned(self):
        self.assertEqual(self.request("/v1/pair/create","POST",data={})[0],403)
        status,created=self.request("/v1/pair/create","POST",bearer=self.vars["AURORA_ADMIN_TOKEN"],data={})
        self.assertEqual(status,200)
        pair=created["pair_code"]
        status,claimed=self.request("/v1/pair/claim","POST",data={"pair_code":pair})
        self.assertEqual(status,200)
        self.assertEqual(self.request("/v1/pair/claim","POST",data={"pair_code":pair})[0],403)
        owner=claimed["session"]
        _,items=self.request("/v1/versions",bearer=owner)
        self.assertEqual(items["versions"][0]["version"],"1.6.15.3.build.245")
        self.assertNotIn("object_key",items["versions"][0])
        status,download=self.request("/v1/download?id=sdv-1.6.15.3-b245",bearer=owner)
        self.assertEqual(status,200)
        self.assertIn("X-Amz-Expires=900",download["url"])
        self.assertIn("d0ab9fdebeadcc640b3fc0324da411b3.r2.cloudflarestorage.com",download["url"])
        self.assertNotIn(self.vars["AURORA_R2_SECRET_ACCESS_KEY"],download["url"])
        self.assertFalse(app.authorize(owner+"invalid"))

    def test_requires_owner_private_rights_and_safe_paths(self):
        bad=json.loads(self.vars["AURORA_PRIVATE_CATALOG_JSON"])
        bad[0]["rights"]="public"
        with patch.dict(os.environ,{"AURORA_PRIVATE_CATALOG_JSON":json.dumps(bad)}):
            self.assertFalse(app.configured())
        bad[0]["rights"]="owner-private-backup"
        bad[0]["object_key"]="../escape.apks"
        with patch.dict(os.environ,{"AURORA_PRIVATE_CATALOG_JSON":json.dumps(bad)}):
            self.assertFalse(app.configured())

if __name__=="__main__":unittest.main()
