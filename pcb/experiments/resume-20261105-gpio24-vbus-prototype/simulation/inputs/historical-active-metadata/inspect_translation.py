#!/usr/bin/env python3
"""Read-only expanded-netlist inspection; no simulation or vendor edits."""
import ctypes,sys,pathlib
P=pathlib.Path(sys.argv[1]).resolve();out=pathlib.Path(sys.argv[2]).resolve();out.mkdir(exist_ok=True,parents=True)
wave=out/'waveform.txt'
if wave.exists(): wave.unlink() # A failed rerun must never reuse a stale waveform.
lib=ctypes.CDLL('libngspice.so.0')
logs=[]
live_log=(out/"ngspice.log").open("w")
CB=ctypes.CFUNCTYPE(ctypes.c_int,ctypes.c_char_p,ctypes.c_int,ctypes.c_void_p)
EXIT=ctypes.CFUNCTYPE(ctypes.c_int,ctypes.c_int,ctypes.c_bool,ctypes.c_bool,ctypes.c_int,ctypes.c_void_p)
@CB
def log(s,i,u):
 line=s.decode(errors='replace');logs.append(line);live_log.write(line+'\n');live_log.flush();return 0
@CB
def stat(s,i,u):return 0
@EXIT
def ex(s,im,quit,i,u):logs.append(f'CONTROLLED_EXIT {s} {im} {quit}');return 0
lib.ngSpice_Init.argtypes=[CB,CB,EXIT,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p]
lib.ngSpice_Init.restype=ctypes.c_int
lib.ngSpice_Command.argtypes=[ctypes.c_char_p];lib.ngSpice_Command.restype=ctypes.c_int
lib.ngSpice_Init(log,stat,ex,None,None,None,None)
def cmd(s):
 code=lib.ngSpice_Command(s.encode());line=f'COMMAND_RETURN {s}: {code}';logs.append(line);live_log.write(line+'\n');live_log.flush();return code
import os
cmd('set ngbehavior='+os.environ.get('NGSPICE_COMPAT','ps'))
cmd('set numdgt=12')
cmd('version')
import json
for mod in json.loads((pathlib.Path(__file__).resolve().parent/'installation.json').read_text())['modules']:
 cmd('codemodel '+mod['path'])
cmd('source '+str(P))
cmd('listing e')
live_log.close()
(out/'ngspice.log').write_text('\n'.join(logs)+'\n')
print('Read-only expanded circuit listing recorded; no analysis run.')
