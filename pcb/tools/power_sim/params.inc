* Nominal parameter set. run_power_sim.py writes a copy of this file with
* corner values into each run directory; this one is used when a deck is
* run by hand.
* --- source ---
.param vsrc=5.0
* source + cable resistance, as given for the analysis
.param rsrc=0.25
* cable loop inductance [ASSUMED 1 uH, about 1 m]; 200 Ohm in parallel
* stands for cable loss at the ringing frequency [ASSUMED]
.param lcab=1u
.param rfuse=0.132
* --- capacitors, effective values under DC bias ---
* C125, C126 1 uF 50 V X7R 0603 at 5 V [ASSUMED -10 %]
.param c125=0.9u
.param c126=0.9u
* C136 + C137 10 uF 25 V 0603: 4.7 uF each at 5 V [Samsung data, qa/datasheet-review]
.param cin=9.4u
* C140 + C141 22 uF 10 V 0603: 8.7 uF each at 4 V [Samsung data]
.param cloc=17.4u
* C100 22 uF 25 V 1206: 15.8 uF at 4 V [Samsung data]
.param c100=15.8u
* C120 1 uF 25 V X5R 0402 at 4 V [ASSUMED -45 %]
.param c120=0.55u
* C101 4.7 uF 50 V X7R 1206 at 3.3 V [ASSUMED -4 %]
.param c101=4.5u
* C102 4.7 uF 6.3 V 0402 at 3.3 V [ASSUMED -40 %] + 12 x 100 nF [ASSUMED -5 %]
.param c33m=3.94u
* LED rail: C121 4.7 uF 0402 at 4 V [ASSUMED -60 %] + 78 x 100 nF [ASSUMED -10 %]
.param cled=8.9u
* --- parts ---
.param l2=4.7u
.param dcr=0.0401
.param css=100n
.param r121=154k
.param ilim=0.5
.param kdvdt=1
.param ronef=0.0282
.param rtrin=0.224
.param vldo=3.3
.param rdo=0.417
.param fugb=100k
.param ios=0.2015
* C143, feed-forward capacitor across R159 (TPS6293x data sheet 10.2.2.10). 1f = not fitted.
.param cff=22p
.param kea=1
.param vref=0.8
.param iss=5.5u
* --- loads ---
.param i33a=0.020
.param i33b=0.120
.param iled=0.150
