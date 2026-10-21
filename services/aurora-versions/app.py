"""Private Aurora version catalog and short-lived R2 GET URLs.

For owner-authorized personal backups and artifacts with redistribution rights only.
Never store R2 keys in an APK. Do not deploy without env secrets.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import re
import secrets
import threading
import time
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PAIRINGS = {}
LOCK = threading.Lock()
ID = re.compile(r"^[a-zA-Z0-9._-]{1,70}$")
ACCOUNT = re.compile(r"^[0-9a-fA-F]{32}$")
HEX = re.compile(r"^[0-9a-fA-F]{64}$")
REQUIRED_ENV = ("AURORA_ADMIN_TOKEN", "AURORA_SESSION_SECRET",
    "AURORA_R2_ACCOUNT_ID","AURORA_R2_BUCKET","AURORA_R2_ACCESS_KEY_ID",
    "AURORA_R2_SECRET_ACCESS_KEY","AURORA_PRIVATE_CATALOG_JSON")


def b64(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode("ascii")


def unb64(v: str) -> bytes:
    return base64.urlsafe_b64decode(v+"="*((-len(v))%4))


def catalog():
    raw = json.loads(os.environ["AURORA_PRIVATE_CATALOG_JSON"])
    if not isinstance(raw, list) or len(raw) > 30:
        raise ValueError("Invalid catalog")
    results = []
    used = set()
    for row in raw:
        if not isinstance(row, dict):
            raise ValueError("Invalid catalog entry")
        ident = row.get("id")
        version = row.get("version")
        key = row.get("object_key")
        digest = row.get("sha256")
        size = row.get("size")
        if not isinstance(ident, str) or not ID.fullmatch(ident) or ident in used:
            raise ValueError("Invalid or duplicate id")
        if not isinstance(version, str) or not re.fullmatch(r"[0-9A-Za-z._+-]{1,60}",version):
            raise ValueError("Invalid version")
        if (not isinstance(key,str) or not key or len(key)>200 or key.startswith("/")
            or ".." in key.split("/") or not key.lower().endswith(".apks")):
            raise ValueError("Invalid archive path")
        if not isinstance(digest,str) or not HEX.fullmatch(digest):
            raise ValueError("Expected SHA256 required")
        if not isinstance(size,int) or not (1_000_000 <= size <= 5_000_000_000):
            raise ValueError("Invalid archive size")
        if row.get("rights") != "owner-private-backup":
            raise ValueError("Only owner private backup metadata accepted")
        used.add(ident)
        results.append({"id":ident,"version":version,"size":size,
            "sha256":digest.lower(),"object_key":key})
    return results


def configured() -> bool:
    try:
        return (all(os.environ.get(name) for name in REQUIRED_ENV)
            and ACCOUNT.fullmatch(os.environ["AURORA_R2_ACCOUNT_ID"]) is not None
            and len(os.environ["AURORA_ADMIN_TOKEN"])>=24
            and len(os.environ["AURORA_SESSION_SECRET"])>=32
            and bool(catalog()))
    except (ValueError, TypeError, KeyError, json.JSONDecodeError):
        return False


def token(subject: str, lifetime: int = 30*24*3600) -> str:
    data = json.dumps({"sub":subject,"exp":int(time.time())+lifetime},
        separators=(",",":"),sort_keys=True).encode()
    signed = b64(data)
    key = os.environ["AURORA_SESSION_SECRET"].encode()
    tag = b64(hmac.new(key,signed.encode(),hashlib.sha256).digest())
    return signed+"."+tag


def authorize(value: str) -> bool:
    if len(value)>1024 or "." not in value:
        return False
    try:
        signed, tag = value.split(".",1)
        calc=b64(hmac.new(os.environ["AURORA_SESSION_SECRET"].encode(),
            signed.encode(),hashlib.sha256).digest())
        if not hmac.compare_digest(calc,tag):
            return False
        data=json.loads(unb64(signed))
        return data.get("sub")=="aurora-owner" and int(data.get("exp",0))>time.time()
    except (ValueError,KeyError,TypeError,base64.binascii.Error):
        return False


def hsign(key: bytes, value: str) -> bytes:
    return hmac.new(key,value.encode(),hashlib.sha256).digest()


def presign(item: dict, *, now: int | None = None, ttl: int = 900) -> str:
    import datetime
    account=os.environ["AURORA_R2_ACCOUNT_ID"].lower()
    bucket=os.environ["AURORA_R2_BUCKET"]
    access=os.environ["AURORA_R2_ACCESS_KEY_ID"]
    secret=os.environ["AURORA_R2_SECRET_ACCESS_KEY"]
    when=datetime.datetime.fromtimestamp(now or time.time(),datetime.timezone.utc)
    stamp=when.strftime("%Y%m%dT%H%M%SZ")
    day=stamp[:8]
    scope=f"{day}/auto/s3/aws4_request"
    host=account+".r2.cloudflarestorage.com"
    obj=urllib.parse.quote(item["object_key"],safe="/-._~")
    path="/"+urllib.parse.quote(bucket,safe="-._~")+"/"+obj
    fields={
        "X-Amz-Algorithm":"AWS4-HMAC-SHA256",
        "X-Amz-Credential":access+"/"+scope,
        "X-Amz-Date":stamp,
        "X-Amz-Expires":str(ttl),
        "X-Amz-SignedHeaders":"host",
    }
    query=urllib.parse.urlencode(sorted(fields.items()),quote_via=urllib.parse.quote,safe="-._~")
    req="GET\n"+path+"\n"+query+"\nhost:"+host+"\n\nhost\nUNSIGNED-PAYLOAD"
    tosign="AWS4-HMAC-SHA256\n"+stamp+"\n"+scope+"\n"+hashlib.sha256(req.encode()).hexdigest()
    secretkey=("AWS4"+secret).encode()
    for piece in (day,"auto","s3","aws4_request"):
        secretkey=hsign(secretkey,piece)
    signature=hsign(secretkey,tosign).hex()
    return "https://"+host+path+"?"+query+"&X-Amz-Signature="+signature


class Handler(BaseHTTPRequestHandler):
    server_version="AuroraVersions/1"
    def log_message(self, fmt, *args):
        # Never log pairing codes, Bearer tokens or presigned URLs.
        print("request served", flush=True)

    def response(self, status, payload):
        raw=json.dumps(payload,separators=(",",":"),ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type","application/json; charset=utf-8")
        self.send_header("Cache-Control","no-store")
        self.send_header("X-Content-Type-Options","nosniff")
        self.send_header("Content-Length",str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def read_data(self):
        try:
            length=int(self.headers.get("Content-Length","0"))
            if length<1 or length>2048:
                raise ValueError("Bad payload")
            return json.loads(self.rfile.read(length))
        except Exception:
            return None

    def device_allowed(self):
        header=self.headers.get("Authorization","")
        return header.startswith("Bearer ") and authorize(header[7:])

    def admin_allowed(self):
        supplied=self.headers.get("Authorization","")
        expected="Bearer "+os.environ["AURORA_ADMIN_TOKEN"]
        return hmac.compare_digest(supplied,expected)

    def do_GET(self):
        path=urllib.parse.urlsplit(self.path).path
        if path=="/health":
            return self.response(200,{"ready":configured()})
        if not configured():
            return self.response(503,{"error":"owner server setup required"})
        if not self.device_allowed():
            return self.response(401,{"error":"owner pairing required"})
        if path=="/v1/versions":
            return self.response(200,{"schema":"aurora-owner-versions/v1",
                "versions":[{k:v for k,v in item.items() if k!="object_key"}
                    for item in catalog()]})
        if path=="/v1/download":
            params=urllib.parse.parse_qs(urllib.parse.urlsplit(self.path).query)
            ident=params.get("id",[""])[0]
            item=next((x for x in catalog() if x["id"]==ident),None)
            if item is None:
                return self.response(404,{"error":"version missing"})
            return self.response(200,{"url":presign(item),"ttl_seconds":900,
                "sha256":item["sha256"],"size":item["size"]})
        return self.response(404,{"error":"unknown endpoint"})

    def do_POST(self):
        path=urllib.parse.urlsplit(self.path).path
        if not configured():
            return self.response(503,{"error":"owner server setup required"})
        if path=="/v1/pair/create":
            if not self.admin_allowed():
                return self.response(403,{"error":"admin only"})
            with LOCK:
                now=time.time()
                for key,deadline in list(PAIRINGS.items()):
                    if deadline<now:del PAIRINGS[key]
                if len(PAIRINGS)>10:return self.response(429,{"error":"too many codes"})
                code=secrets.token_urlsafe(24)
                PAIRINGS[code]=now+180
            return self.response(200,{"pair_code":code,"expires_seconds":180})
        if path=="/v1/pair/claim":
            body=self.read_data()
            code=body.get("pair_code") if isinstance(body,dict) else None
            if not isinstance(code,str) or len(code)>100:
                return self.response(400,{"error":"invalid pairing"})
            with LOCK:
                expires=PAIRINGS.pop(code,0)
            if expires<time.time():
                return self.response(403,{"error":"pairing expired"})
            return self.response(200,{"session":token("aurora-owner"),"expires_days":30})
        return self.response(404,{"error":"unknown endpoint"})


def main():
    # Safe initial deployment without keys: health is ready=false and private
    # endpoints return 503 until the owner configures R2 and server secrets.
    port=int(os.environ.get("PORT","8080"))
    ThreadingHTTPServer(("0.0.0.0",port),Handler).serve_forever()


if __name__=="__main__":main()
