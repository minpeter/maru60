# Keyboard studio v7.1 backup

Readable original release source; existing repository design and licenses unchanged.
See README.txt for Blender 4.3.2 reproduction commands and SOURCE.txt for exact historical shell provenance. The shell is printed v7.4 at commit 96a59b2d17d79c40edf089e3ff11a7d0475d2724, not current branch geometry.

All 60 key meshes are procedurally generated from keycaps_v7_1/layout.json; UV placement, texture legends and material configuration are included. The packed Blender scene contains the full assembled scene. Text is rasterized: no editable original font files are claimed. CapsLock left platform 17.5 mm and 3.2 mm drop are photo-derived estimates. Kiro is continuous uniform purple without a lighter patch; FriendliAI blue and Upstage white. YongQiu Retro Programmer 143 VIM legend wording, including printed typos, is preserved; typography/materials are approximate.

No raw personal reference photos/videos, authentication screenshots or private logs are added. Logo shapes are third-party marks, not a commercial rights grant. Existing repository licenses remain authoritative; this backup does not relicense third-party content.

The original 72 RGBA 1024x1536 PNGs are hashed in final_frame_checksums.json; to avoid 229 MB of redundant outputs they are reproducible rather than all duplicated here. Web-ready full rotation and a full-resolution sample accompany the sources. No 72-frame render was re-run for this backup.

The packed scene is stored losslessly gzip-compressed: `gunzip -k keyboard_studio_v7_1.blend.gz` before opening it. CHECKSUMS.json records the uncompressed original.
