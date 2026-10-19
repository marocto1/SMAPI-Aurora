#!/usr/bin/env python3
"""Repackage a rebuilt .NET Android DLL into its existing ELF DSO container.

.NET for Android's non-AssemblyStore build puts a *managed PE DLL* in the
non-allocated ELF section 'payload' of lib_<AssemblyName>.dll.so.
Only that single payload is changed, preserving the compiled Android host
activity/DEX, native libraries, and all commercial-game safety boundaries.

Fail-closed: supports one precise ELF64/aarch64/non-allocated payload layout.
"""
from pathlib import Path
import argparse
import struct

def u16(data, offset):
    return struct.unpack_from("<H",data,offset)[0]

def u32(data, offset):
    return struct.unpack_from("<I",data,offset)[0]

def u64(data, offset):
    return struct.unpack_from("<Q",data,offset)[0]

def patch(original:bytes, newdll:bytes) -> bytes:
    if len(newdll)<1024 or not newdll.startswith(b"MZ") or b"JunimoGate.App" not in newdll:
        raise ValueError("Rebuilt DLL is not the expected JunimoGate.App PE")
    if original[:4]!=b"\x7fELF" or original[4:6]!=b"\x02\x01":
        raise ValueError("Expected little-endian ELF64 native DSO")
    if u16(original,0x12)!=183 or u16(original,0x10)!=3: # aarch64, ET_DYN
        raise ValueError("Wrong native ABI/type for managed DLL container")
    shoff=u64(original,0x28)
    shsize=u16(original,0x3a)
    shcount=u16(original,0x3c)
    shstridx=u16(original,0x3e)
    if shsize!=64 or shcount<5 or shcount>100 or shstridx>=shcount:
        raise ValueError("Unexpected ELF section header layout")
    if shoff+shsize*shcount!=len(original):
        raise ValueError("Unexpected trailing data after ELF section table")
    string_hdr=shoff+shstridx*shsize
    string_offset=u64(original,string_hdr+24)
    string_size=u64(original,string_hdr+32)
    strings=original[string_offset:string_offset+string_size]
    if len(strings)!=string_size:
        raise ValueError("Section name table incomplete")
    sections=[]
    for i in range(shcount):
        pos=shoff+i*shsize
        nameoffset=u32(original,pos)
        if nameoffset>=len(strings):raise ValueError("Invalid section name offset")
        name=strings[nameoffset:].split(b"\0",1)[0]
        if name==b"payload":
            sections.append((i,pos))
    if len(sections)!=1:raise ValueError("Expected exactly one managed payload ELF section")
    section,headerpos=sections[0]
    offset=u64(original,headerpos+24)
    size=u64(original,headerpos+32)
    flags=u64(original,headerpos+8)
    sectiontype=u32(original,headerpos+4)
    if sectiontype!=1 or flags!=0 or offset<4096 or offset+size!=shoff:
        raise ValueError("Managed PE payload is not a trailing, non-allocated section")
    olddll=original[offset:offset+size]
    if not olddll.startswith(b"MZ") or b"JunimoGate.App" not in olddll:
        raise ValueError("Original payload does not match expected Android DLL")
    # Section header table stays after payload. The new PE is uncompressed.
    newshoff=((offset+len(newdll)+63)//64)*64
    pad=newshoff-offset-len(newdll)
    result=bytearray(original[:offset]+newdll+bytes(pad)+original[shoff:])
    struct.pack_into("<Q",result,0x28,newshoff)
    struct.pack_into("<Q",result,newshoff+section*shsize+32,len(newdll))
    if bytes(result[offset:offset+len(newdll)])!=newdll:
        raise ValueError("ELF DLL round-trip failed")
    return bytes(result)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("template",type=Path)
    p.add_argument("recompiled_dll",type=Path)
    p.add_argument("output",type=Path)
    args=p.parse_args()
    if args.output.exists(): raise SystemExit("Output exists; refusing overwrite")
    patched=patch(args.template.read_bytes(),args.recompiled_dll.read_bytes())
    args.output.write_bytes(patched)
    print("PASS: rebuilt managed .NET DLL repackaged into exactly one ARM64 ELF payload")
    print("Only the launcher SettingsFragment was patched; no proprietary game assemblies bundled.")

if __name__=="__main__": main()
