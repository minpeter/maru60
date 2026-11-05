#!/usr/bin/env python3
from pathlib import Path
import numpy as np
import os
os.environ.setdefault("MPLCONFIGDIR","/tmp/v7-ngspice-matplotlib")
os.environ.setdefault("XDG_CACHE_HOME","/tmp/v7-ngspice-cache")
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
r=Path(__file__).resolve().parent
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
fig,ax=plt.subplots(3,1,figsize=(10,10),layout='constrained')
a=np.loadtxt(r/'runs/u7-original-internal-probes/waveform.txt',skiprows=1)
ax[0].plot(a[:,0]*1e3,a[:,1],label='EN input (V)');ax[0].plot(a[:,0]*1e3,a[:,2],label='Output (V)');ax[0].plot(a[:,0]*1e3,a[:,5],label='Internal ENOK (0/1)',ls='--')
ax[0].set(title='U7: rejected semantics. EN-high incorrectly makes ENOK low.',xlabel='Time (ms)',ylabel='Voltage (V)');ax[0].legend(loc='upper right',ncol=3)
b=np.loadtxt(r/'runs/buck-original-portability/waveform.txt',skiprows=1)
ax[1].plot(b[::30,0]*1e3,b[::30,1],label='Input (V)');ax[1].plot(b[::30,0]*1e3,b[::30,2],label='Output (V)');ax[1].axhline(4,color='gray',ls=':',label='Requested 4 V target')
ax[1].set(title='Buck: 5 V exploratory bench does not regulate; convergence warnings.',xlabel='Time (ms)',ylabel='Voltage (V)');ax[1].legend(loc='center right',ncol=3)
c=np.loadtxt(r/'runs/buck-diagnostic-24v/waveform.txt',skiprows=1);tstop=c[-1,0]*1e3
ax[2].plot(c[::20,0]*1e3,c[::20,2],label='Partial output (V)');ax[2].axhline(5,color='gray',ls=':',label='Requested 5 V target');ax[2].axvline(tstop,color='#b22222',ls='--',label=f'Aborted at {tstop:.6f} ms');ax[2].axvspan(tstop,6,color='#eeeeee');ax[2].text(3.7,2.5,'No simulated result',ha='center',color='#777777')
ax[2].set(title='Buck: self-authored 24 V diagnostic aborts before requested 6 ms.',xlabel='Time (ms)',ylabel='Voltage (V)',xlim=(0,6));ax[2].legend(loc='upper right')
for a in ax:a.grid(alpha=.2)
fig.suptitle('Runtime diagnostics only: NOT validated hardware predictions',fontweight='bold',color='#a32121',fontsize=14)
fig.savefig(r/'runtime-diagnostics.png',dpi=150)
