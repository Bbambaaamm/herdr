# Anatomical mesh attribution

The numeric vertex/triangle arrays in `face-anatomy.js` are derived from Google's MediaPipe canonical face model, under Apache License 2.0. The complete license is included in `face-anatomy-LICENSE.txt`.

- Upstream repository: https://github.com/google-ai-edge/mediapipe
- Pinned upstream commit: `83766a67be28136dee18e6449809677bb5a0a219`
- Original path: `mediapipe/modules/face_geometry/data/canonical_face_model.obj`
- Original file SHA-256: `8bac80443397e113f41a8b565ea72c59390bc031d9defab289dba7bc0c54e618`
- Retrieved 2026-09-25. Original has 468 vertices and 898 triangles.

Changes: parsed OBJ position and triangle indices into JavaScript arrays; omitted UV coordinates. Runtime model rescales coordinates, opens anatomical eye/mouth apertures, adds jaw skinning, a back cranium, independently movable eyes, and procedural mechanical geometry.

No film asset, film 3D model or user reference image is embedded in the runtime scene. This is an original mechanical treatment of a redistributable anatomical template, not the original Deus Ex Machina production asset.
