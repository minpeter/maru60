Three-reference legibility correction, prototype candidate

U13,R135,R145 references grow0.75→0.80mm while retaining0.10mm strokes, visibility, mirrored B.Silkscreen and names. New poses: U13(89.8,45.3),angle0; R135(117.4,36.4),angle0; R145(117.8,38.5),angle90. No footprint pose, copper, drill, filled zone, rule, other field or companion changes. Exact raw reversal restores source56d66f65 byte-for-byte.

Fresh DRC50→44 warnings: exactly six named text-height/mask/silk records disappear; none appear. Ten full physical open-component pairs remain; native representative endpoints can change and are explicitly reconciled. Material behavior is inherited only through exact electrical-byte identity, not claimed as a new electrical simulation. Cold58-file refill is byte-identical.

Native actual-ink checks pass mask, other silk, Fab, courtyard and edge tests. Independent raw closed-centerline and drawn-stroke courtyard checks both exceed0.20mm: minimum stroke-envelope gaps0.239895mm(U13),0.204523mm(R135),0.271800mm(R145). Native cached courtyard values are separately recorded. Mirrored native images were visually inspected: U13 is directly below its package; R135 and R145 sit clearly beside their own parts. These are2D source proxies, not real3D assembly or fabrication approval.

Inherits all prototype and strict-no-loss limitations of56d66f65; strict04be baseline remains unchanged. No hiding/deletion of labels, rule relaxation or electrical-improvement claim.
