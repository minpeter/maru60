#!/usr/bin/env python3
"""Small ngspice shared-library runner; one circuit per process."""
import ctypes,sys,pathlib
P=pathlib.Path(sys.argv[1]).resolve();out=pathlib.Path(sys.argv[2]).resolve();out.mkdir(exist_ok=True,parents=True)
wave=out/'waveform.txt'
if wave.exists(): wave.unlink() # A failed rerun must never reuse a stale waveform.
lib=ctypes.CDLL('libngspice.so.0')
logs=[]
CB=ctypes.CFUNCTYPE(ctypes.c_int,ctypes.c_char_p,ctypes.c_int,ctypes.c_void_p)
EXIT=ctypes.CFUNCTYPE(ctypes.c_int,ctypes.c_int,ctypes.c_bool,ctypes.c_bool,ctypes.c_int,ctypes.c_void_p)
@CB
def log(s,i,u):
 logs.append(s.decode(errors='replace'));return 0
@CB
def stat(s,i,u):return 0
@EXIT
def ex(s,im,quit,i,u):logs.append(f'CONTROLLED_EXIT {s} {im} {quit}');return 0
lib.ngSpice_Init.argtypes=[CB,CB,EXIT,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p]
lib.ngSpice_Init.restype=ctypes.c_int
lib.ngSpice_Command.argtypes=[ctypes.c_char_p];lib.ngSpice_Command.restype=ctypes.c_int
lib.ngSpice_Init(log,stat,ex,None,None,None,None)
def cmd(s):
 code=lib.ngSpice_Command(s.encode());logs.append(f'COMMAND_RETURN {s}: {code}');return code
cmd('set ngbehavior=ps')
cmd('set numdgt=12')
cmd('version')
cmd('source '+str(P))
cmd('run')
cmd('set wr_singlescale')
cmd('set wr_vecnames')
cmd('wrdata '+str(out/'waveform.txt')+' '+' '.join(sys.argv[3:]))
(out/'ngspice.log').write_text('\n'.join(logs)+'\n')
print('\n'.join(logs[-20:]))
if not wave.exists() or any('Simulation interrupted' in line or 'circuit not parsed' in line for line in logs):sys.exit(1)
