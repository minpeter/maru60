from pathlib import Path
import itertools,json
root=Path(__file__).resolve().parent
vendor=Path('../v7-recovered-library-20261104/extracted/v7-power-simulation/vendor/SLUM808/TPS62932_PSPICE_TRANS/TPS62932_TRANS.LIB').resolve()
lines=['Original TPS62932 subcircuit static logic checks',f'.include {vendor}','Vzero z 0 0','Vone o 0 1'];expect={}
for gate,arity,fn in [('NAND2',2,lambda a,b:1-(a and b)),('AND2',2,lambda a,b:a and b),('AND3',3,lambda a,b,c:a and b and c),('NOR2',2,lambda a,b:1-(a or b)),('OR2',2,lambda a,b:a or b),('INV',1,lambda a:1-a),('BUF',1,lambda a:a),('COMP',2,lambda a,b:int(a>b)),('MUX2',3,lambda a,b,s:b if s else a)]:
 for bits in itertools.product([0,1],repeat=arity):
  name=gate.lower()+''.join(map(str,bits));nodes=' '.join('o' if b else 'z' for b in bits)
  lines.append(f'X{name} {nodes} y{name} {gate}_BASIC_GEN');expect[f'v(y{name})']=int(fn(*bits))
lines+=['.op','.end'];(root/'netlists/buck-original-static-logic.cir').write_text('\n'.join(lines)+'\n');(root/'netlists/buck-original-static-logic-expected.json').write_text(json.dumps(expect,indent=2)+'\n')
# This is a synthetic semantic control of the vendor LIMIT form, not an edited vendor model.
lines=['Synthetic reversed LIMIT semantic control','Vin input 0 0','Erev reversed 0 VALUE { LIMIT(V(input),5,0) }','Eord ordered 0 VALUE { LIMIT(V(input),0,5) }','.dc Vin -1 6 .5','.end'];(root/'netlists/reversed-limit-control.cir').write_text('\n'.join(lines)+'\n')
