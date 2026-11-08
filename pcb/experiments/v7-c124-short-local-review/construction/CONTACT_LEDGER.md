# Exact expanded V4 contact ledger

Source SHA-256: 7c23d6ea36b158fa706fa3e05f0e1f10fa4aa435deecb2d3bcd38c71cf9f8cb1

Analytical native geometry, not constructed CAD. Areas are mm²; actual drill holes are subtracted. The JSON file is the complete ledger.

## Nine old pad contacts replaced

- GND via `763086b7-5549-4f5e-bb08-ce25387b3627` ↔ C124.2 `f79380d7-c89c-4396-b53e-4918d8902c13`: 0.0091025205225
- GND track `19181a2b-164e-4055-9004-2860bebe32f4` ↔ C124.2 `f79380d7-c89c-4396-b53e-4918d8902c13`: 0.1057077651040
- GND track `abcd4fb1-881b-43f9-906e-39d93366692e` ↔ R121.2 `437d8abf-8e4f-4587-99b7-93c610dd4000`: 0.1183915660970
- USB_DVDT track `18d72adc-e983-48eb-b7d1-3047b981e17d` ↔ C124.1 `e99fab95-384f-4c82-aa22-4b94524bb476`: 0.0326711629400
- USB_DVDT track `3aa399c7-b37b-4cb6-b1bb-33266155cd74` ↔ C124.1 `e99fab95-384f-4c82-aa22-4b94524bb476`: 0.0282778110580
- USB_DVDT track `3dce1fa7-ff7a-5b39-a41c-9aedbc2eba57` ↔ C124.1 `e99fab95-384f-4c82-aa22-4b94524bb476`: 0.0500855814700
- USB_DVDT track `5b54e93a-0faf-402b-8565-7a7da068e6bb` ↔ C124.1 `e99fab95-384f-4c82-aa22-4b94524bb476`: 0.0214211629400
- USB_DVDT track `c69210ed-fc0a-5e8b-994b-e205b18141f3` ↔ C124.1 `e99fab95-384f-4c82-aa22-4b94524bb476`: 0.0344416127895
- USB_OVLO track `05a0b97d-79af-50e5-b191-fe26b55d2c02` ↔ R121.1 `2ceda713-c41e-4c74-9962-f6a642f1e236`: 0.0882516776210

## New to retained native contacts

- R121.2 → GND track `abcd4fb1-881b-43f9-906e-39d93366692e`: 0.0551031427770
- old-ground-bridge → GND via `763086b7-5549-4f5e-bb08-ce25387b3627`: 0.0478458239865
- old-ground-bridge → GND track `19181a2b-164e-4055-9004-2860bebe32f4`: 0.1264155302080
- old-ground-bridge → GND track `abcd4fb1-881b-43f9-906e-39d93366692e`: 0.0411650268745
- UVLO0 → USB_UVLO track `751dcade-77aa-4c93-aab3-170f1229e0e4`: 0.0177152035110
- UVLO0 → USB_UVLO track `78c0ab16-8ae4-4d8f-93ff-7810ecf41eed`: 0.0038718109395
- UVLO5 → USB_UVLO track `7d18b97e-b287-4393-8a28-411c96dcc305`: 0.0181318794495
- UVLO5 → USB_UVLO track `c206500a-2fd7-49e9-ac49-5158c4d9181e`: 0.0026191701635
- UVLO5 → USB_UVLO track `d2cb1d31-5b41-48bd-9989-7d76f6912b59`: 0.0077669043770
- OVLO7 → USB_OVLO track `e218cfe4-e4ba-5b6c-985d-8f1da39a4402`: 0.0176909461760
- DVDT0 → USB_DVDT track `7c494a73-d1ac-5d4f-ae2d-7b26d0b153f3`: 0.0177922090430
- DVDT0 → U8.7 `e07df864-b2ae-41c6-8b80-01729167b27e`: 0.0238355814700
- DVDT0 → U8.7 `e5357bcd-1b36-4b99-a325-1f57b9e1a8b7`: 0.0115896856990
- DVDT1 → U8.7 `e5357bcd-1b36-4b99-a325-1f57b9e1a8b7`: 0.0015896636940
- GND0 → GND via `8e0fa85d-f2bc-543d-aae7-d8f6ff75061a`: 0.0193746831795
- GND0 → GND track `406d468c-87d5-5b67-aa13-7b2d4d7263d4`: 0.0176720323510

## Existing six-object direct ground component

- GND via `763086b7-5549-4f5e-bb08-ce25387b3627` ↔ GND track `abcd4fb1-881b-43f9-906e-39d93366692e`: 0.0266434479770
- GND via `763086b7-5549-4f5e-bb08-ce25387b3627` ↔ C124.2 `f79380d7-c89c-4396-b53e-4918d8902c13`: 0.0091025205225
- GND via `efadf2be-e519-469f-a84c-2e7cbb60672a` ↔ GND track `19181a2b-164e-4055-9004-2860bebe32f4`: 0.0266434605130
- GND track `19181a2b-164e-4055-9004-2860bebe32f4` ↔ C124.2 `f79380d7-c89c-4396-b53e-4918d8902c13`: 0.1057077651040
- GND track `abcd4fb1-881b-43f9-906e-39d93366692e` ↔ R121.2 `437d8abf-8e4f-4587-99b7-93c610dd4000`: 0.1183915660970

## Precisely bounded track retirement inventory

- USB_OVLO `05a0b97d-79af-50e5-b191-fe26b55d2c02`: [15.05, 19.925] → [14.0, 19.325]; width 0.150; length 1.209338662
- USB_UVLO `0bf33e40-59fe-4d2e-b57a-4f027a536d54`: [13.25, 17.35] → [13.25, 19.65]; width 0.150; length 2.300000000
- USB_UVLO `1274878c-3b2f-48be-b335-ff839fe8150d`: [14.85, 21.05] → [16.8, 21.05]; width 0.150; length 1.950000000
- USB_UVLO `17c10e7b-5920-47bd-8de6-90bf22d6522c`: [14.65, 20.95] → [14.7, 21.0]; width 0.150; length 0.070710678
- USB_DVDT `18d72adc-e983-48eb-b7d1-3047b981e17d`: [15.65, 19.3] → [15.55, 19.3]; width 0.150; length 0.100000000
- USB_UVLO `1cad25a0-be8b-4cb5-8379-06fa21c6eea4`: [14.3, 20.8] → [14.35, 20.8]; width 0.150; length 0.050000000
- USB_UVLO `2bef712b-2271-470e-9ed0-961aa43325cd`: [13.45, 17.05] → [13.3, 17.2]; width 0.150; length 0.212132034
- USB_UVLO `33383b43-6318-422d-a220-1199026db482`: [14.8, 21.0] → [14.85, 21.05]; width 0.150; length 0.070710678
- USB_UVLO `3a13a9a0-dbbd-42a5-ad34-f1171f7bdf93`: [13.25, 19.65] → [13.3, 19.7]; width 0.150; length 0.070710678
- USB_DVDT `3aa399c7-b37b-4cb6-b1bb-33266155cd74`: [15.55, 19.3] → [15.5, 19.25]; width 0.150; length 0.070710678
- USB_DVDT `3dce1fa7-ff7a-5b39-a41c-9aedbc2eba57`: [17.25, 19.4] → [15.7, 19.4]; width 0.150; length 1.550000000
- USB_UVLO `4174a692-19ae-4049-916a-e21e775415e2`: [13.3, 19.7] → [13.3, 19.8]; width 0.150; length 0.100000000
- USB_DVDT `5b54e93a-0faf-402b-8565-7a7da068e6bb`: [15.5, 19.275] → [15.5, 19.25]; width 0.150; length 0.025000000
- USB_UVLO `681a81ab-2f2d-4b74-b71a-83e09245dca9`: [14.35, 20.8] → [14.4, 20.85]; width 0.150; length 0.070710678
- USB_UVLO `800b2e7b-f1bf-428e-b54f-6431e8b4af81`: [13.3, 19.8] → [14.3, 20.8]; width 0.150; length 1.414213562
- USB_UVLO `8305ea6c-327f-407d-9092-892db2d90da5`: [14.2, 16.35] → [13.5, 17.05]; width 0.150; length 0.989949494
- USB_UVLO `8a91626f-c454-43dc-876d-58c563ab2be4`: [14.4, 20.85] → [14.45, 20.85]; width 0.150; length 0.050000000
- USB_UVLO `a1d85406-3c20-4dc4-850f-7efdab0cdfd6`: [16.8, 21.05] → [16.85, 21.1]; width 0.150; length 0.070710678
- USB_UVLO `a44d4a9f-aa40-4d02-9ed7-16774fbe4849`: [17.1, 21.15] → [17.2, 21.15]; width 0.150; length 0.100000000
- USB_UVLO `a621cda3-f605-4bff-b3d7-2213de164c79`: [13.3, 17.2] → [13.3, 17.3]; width 0.150; length 0.100000000
- USB_UVLO `b2509e57-5e09-46f8-8514-02052efec7ae`: [14.7, 21.0] → [14.8, 21.0]; width 0.150; length 0.100000000
- USB_UVLO `bca2758e-28c6-41dd-97f0-2c9466f8ca97`: [14.55, 20.9] → [14.6, 20.95]; width 0.150; length 0.070710678
- USB_UVLO `bf30ad55-1b9f-467f-8fef-7ac60c4f920d`: [17.05, 21.1] → [17.1, 21.15]; width 0.150; length 0.070710678
- USB_UVLO `c635b040-8e23-4da7-9cec-9b59b66c88e3`: [14.5, 20.9] → [14.55, 20.9]; width 0.150; length 0.050000000
- USB_DVDT `c69210ed-fc0a-5e8b-994b-e205b18141f3`: [15.7, 19.4] → [15.65, 19.3]; width 0.150; length 0.111803399
- USB_UVLO `d340564d-1097-4e0e-8f38-4b0385b0a0bb`: [14.45, 20.85] → [14.5, 20.9]; width 0.150; length 0.070710678
- USB_UVLO `db0f565d-8915-441b-b9f8-50cdd933467c`: [13.3, 17.3] → [13.25, 17.35]; width 0.150; length 0.070710678
- USB_UVLO `de44c09a-0455-40a8-8f3e-d6d7fa9dcec0`: [16.85, 21.1] → [17.05, 21.1]; width 0.150; length 0.200000000
- USB_OVLO `eb147f3b-fbe7-5ff5-a09d-d36fa376b92f`: [20.175, 21.0] → [15.05, 19.925]; width 0.150; length 5.236530340
- USB_UVLO `efb452e0-b8d1-484b-9a90-3179d99b1aa8`: [13.5, 17.05] → [13.45, 17.05]; width 0.150; length 0.050000000
- USB_UVLO `f0a66333-ec8a-4243-a130-df6b6aa03b1d`: [14.6, 20.95] → [14.65, 20.95]; width 0.150; length 0.050000000
