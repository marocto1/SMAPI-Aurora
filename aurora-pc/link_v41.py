"""Aurora Link 4.1: offline QR display for an already-opened invite.

A QR contains the room bearer token. Show only to trusted friends; closing
and reopening room rotates it. No accounts, relay, persistent token storage.
"""
from __future__ import annotations
import coop_v20 as coop


def invite_qr_payload(invitation: str) -> str:
    ip, token = coop.parse_invite(invitation)
    return coop.make_invite(ip, token)


def generate_qr_image(invitation: str):
    """Return Pillow RGB image; qrcode/pillow bundled into Windows EXE."""
    import qrcode
    code = qrcode.QRCode(version=None,error_correction=qrcode.constants.ERROR_CORRECT_M,
                         box_size=8,border=3)
    code.add_data(invite_qr_payload(invitation))
    code.make(fit=True)
    return code.make_image(fill_color="black",back_color="white").convert("RGB")
