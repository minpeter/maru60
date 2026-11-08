from screen import *
N='EXT_GPIO25'
search(N,p.B_Cu,(107.1,37.325),box=(95.5,29,115,46),step=.025)
pts=json.loads((ROOT/'qa/reach-last.json').read_text());(ROOT/'qa/u11-reach.json').write_text(json.dumps(pts));v=[a for a in pts if viaok(N,a)];(ROOT/'qa/u11-vias.json').write_text(json.dumps(v));print('U11 VIA COUNT',len(v),flush=True)
