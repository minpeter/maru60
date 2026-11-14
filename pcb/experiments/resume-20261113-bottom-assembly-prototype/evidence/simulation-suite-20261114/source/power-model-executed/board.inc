* Candidate-bound resistor network; radial equivalent branches, shared-path coupling approximated.
* Maru60 power tree as built in the 2026-11-11 order candidate.
* Component values: qa/netlist.xml. Parasitics: computed from the board
* geometry (build/order-review/final.json, 35 um copper, 20 C) or assumed.
* Capacitor ESL (below 1 nH) is left out; it only matters above 1 MHz.
* Needs: models.lib, params.inc, and from the deck:
*   Vsrc  src 0 ...            the USB source
*   node  len                  LED enable (GPIO22), 0 / 3.3 V
*   node  i33cmd, ledcmd       load commands in amps (as voltages)
*   node  sh33, shled          short-circuit switches, 0 / 1
* and the buck instance XU18 (averaged or switching), and
*   .param cssx, kdvdtx           soft-start capacitor and eFuse ramp factor
*                                 actually used (decks that only need a settled
*                                 circuit shorten the start-up with these).

* --- source and cable ---
Rsrc  src  n1   {rsrc}
Lcab  n1   vbus {lcab}
* cable loss at the ringing frequency [ASSUMED 200 Ohm across the inductance]
Rcabp n1   vbus 200
* J1 pins to F1: 32 mOhm [CALC from tracks]; F1 SF-1206F100-2 0.132 Ohm +-25 %
Rconn vbus vbf 0.05103
Rf1 vbf vflead {rfuse}
Rfeed vflead vfused 0.013900000000000001

* --- U8 eFuse ---
Cc125 vfused c125e {c125}
Rc125 c125e 0 10m
* snubber across C125: R187 1 Ohm 0805 in series with C144 4.7 uF 50 V X5R 0805.
* It damps the ring of the cable inductance with C125 at plug-in. rsn=1meg: not fitted.
R187  vfused snb {rsn}
Cc144 snb c144e {csn}
Rc144 c144e 0 10m
R120  vfused ovlo 590k
R121  ovlo 0 {r121}
Covlo ovlo 0 3p
R122  vfused uvlo 620k
R123  uvlo 0 267k
Cuvlo uvlo 0 3p
XU8   vfused vprot uvlo ovlo dvdt 0 tps259470a ilim={ilim} kdvdt={kdvdtx} ron={ronef}
R125  dvdt dvc 100
C124  dvc 0 10n
Cc126 vprot c126e {c126}
Rc126 c126e 0 10m

* --- 234 mm x 0.6 mm track to the buck: 0.224 Ohm [CALC], about 60 nH
*     [CALC from 40 Ohm microstrip over the inner ground plane] ---
Rtr1  vprot vp1 {rtrin}
Ltr1  vp1 vbk 60n
* C136 + C137 at the buck input (3.9 / 6.4 mOhm of track each [CALC])
Ccin  vbk cine {cin}
Rcin  cine 0 5m

* --- U18 buck output ---
L2    sw l2x {l2}
Rl2   l2x v4 {dcr}
C139  ss 0 {cssx}
R159  v4 fb 40.0k
C143  v4 fb {cff}
R160  fb 0 10.0k
Cfb   fb 0 5p
* C140 + C141 next to the inductor (5.6 / 14 mOhm of track [CALC])
Ccloc v4 cloce {cloc}
Rcloc cloce 0 6m
D100  v4 vbk pmeg4030
* 37 mm x 0.4 mm to C100 / U2: 43 mOhm [CALC], 20 nH [ASSUMED]
Rtr2 v4 v4x 0.08048000000000001
Ltr2  v4x v4b 20n
Cc100 v4b c100e {c100}
Rc100 c100e 0 3m
* on to U7 / C120: 48 mOhm [CALC], 15 nH [ASSUMED]
Rtr3 v4 v4y 0.08436
Ltr3  v4y v4c 15n
Cc120 v4c c120e {c120}
Rc120 c120e 0 10m

* --- U2 LDO and the 3V3 rail ---
XU2   v4b v33 0 ap2112k33 vset={vldo} rdo={rdo} fugb={fugb}
Cc101 v33 c101e {c101}
Rc101 c101e 0 3m
* LDO to the MCU area, about 30 mm of pour and 0.3 mm track
* [ASSUMED 50 mOhm, 10 nH]
Rtr4 v33 v33x 0.42318
Ltr4  v33x v33m 10n
Cc33m v33m c33me {c33m}
Rc33m c33me 0 5m
R104  v33m avdd 33
C104  avdd 0 2.8u
* 3V3 load: current sink that needs about 2 V to draw anything
* [ASSUMED compliance; the RP2350 core regulator needs 2.7 V]
B33   v33m 0 I = V(i33cmd) * 0.5*(1+tanh((V(v33m)-2.0)/0.3))
S33   v33 0 sh33 0 swsh
* --- U7 LED switch and the LED rail ---
XU7   v4c vled len 0 tps2553 ios={ios}
Ccled vled clede {cled}
Rcled clede 0 5m
R114  vled 0 10k
* 76 x 0.5 mA static [OPSCO SK6805-EC15 Rev A/1], taken as resistive below
* 3 V [ASSUMED]; drive current is a sink that needs about 3 V [ASSUMED]
Bledq vled 0 I = 0.0444 * tanh(max(V(vled),0)/1.5)
Bledd vled 0 I = V(ledcmd) * 0.5*(1+tanh((V(vled)-3.0)/0.2))
Lsh   vled shx 30n
Sled  shx 0 shled 0 swsh
.model swsh sw(vt=0.5 vh=0.1 ron=0.05 roff=100meg)
