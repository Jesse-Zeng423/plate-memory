"""Crop only uniform trailing background from Chrome's RGB/RGBA screenshots."""
import struct
import zlib

SIGNATURE=b'\x89PNG\r\n\x1a\n'


def _chunk(kind,data):
    return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data))


def crop_background(raw,padding=36):
    if not raw.startswith(SIGNATURE):raise ValueError('Invalid PNG signature.')
    chunks=[];cursor=8
    while cursor<len(raw):
        if cursor+12>len(raw):raise ValueError('Truncated PNG chunk.')
        size=struct.unpack('>I',raw[cursor:cursor+4])[0]
        kind=raw[cursor+4:cursor+8];data=raw[cursor+8:cursor+8+size]
        crc=raw[cursor+8+size:cursor+12+size]
        if len(crc)!=4 or struct.unpack('>I',crc)[0]!=zlib.crc32(kind+data):raise ValueError('Invalid PNG checksum.')
        chunks.append((kind,data));cursor+=size+12
    header=next(data for kind,data in chunks if kind==b'IHDR')
    if len(header)!=13:raise ValueError('Invalid PNG header.')
    width,height,depth,color,compression,filtering,interlace=struct.unpack('>IIBBBBB',header)
    if depth!=8 or color not in (2,6) or interlace:return raw
    if not 1<=width<=2000 or not 1<=height<=4000:raise ValueError('PNG dimensions out of bounds.')
    bpp=3 if color==2 else 4;stride=width*bpp
    expected=(stride+1)*height
    decoded=zlib.decompressobj().decompress(b''.join(data for kind,data in chunks if kind==b'IDAT'),expected+1)
    if len(decoded)!=expected:raise ValueError('Invalid PNG scanlines.')
    rows=[];previous=bytearray(stride)
    for y in range(height):
        base=y*(stride+1);mode=decoded[base];row=bytearray(decoded[base+1:base+1+stride])
        if mode not in range(5):raise ValueError('Invalid PNG filter.')
        if mode:
            for x in range(stride):
                a=row[x-bpp] if x>=bpp else 0;b=previous[x];c=previous[x-bpp] if x>=bpp else 0
                if mode==1:value=a
                elif mode==2:value=b
                elif mode==3:value=(a+b)//2
                else:
                    p=a+b-c;pa,pb,pc=abs(p-a),abs(p-b),abs(p-c)
                    value=a if pa<=pb and pa<=pc else b if pb<=pc else c
                row[x]=(row[x]+value)&255
        rows.append(bytes(row));previous=row
    # Only crop when the entire first row is one uniform background color.
    background=rows[0]
    if background!=background[:bpp]*width:return raw
    last=height-1
    while last>0 and rows[last]==background:last-=1
    new_height=min(height,last+1+padding)
    if new_height==height:return raw
    header=struct.pack('>IIBBBBB',width,new_height,depth,color,compression,filtering,interlace)
    result=SIGNATURE+_chunk(b'IHDR',header)
    for kind,data in chunks:
        if kind not in (b'IHDR',b'IDAT',b'IEND'):result+=_chunk(kind,data)
    result+=_chunk(b'IDAT',zlib.compress(b''.join(b'\x00'+row for row in rows[:new_height]),6))
    return result+_chunk(b'IEND',b'')
