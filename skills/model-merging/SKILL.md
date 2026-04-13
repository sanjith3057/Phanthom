# Advanced Model Merging Techniques
**Protocol Status**: Core Functionality

This defines the rules and math applied to fuse intelligence modules into `PHANTOM-3B`.

### Methods Employed
1. **SLERP (Spherical Linear Interpolation)**
   - Used for blending `Qwen2.5-3B-Instruct` with `Qwen2.5-Coder-3B-Instruct`.
   - Modifies vectors directionally over a sphere, preserving semantic vectors better than linear blending.
   
2. **TIES + DARE Fusion**
   - **TIES**: Trims redundant parameters, elects the strongest gradient sign, and averges elements.
   - **DARE**: Randomly zeroes out fine-tuning deltas to restore baseline stability, followed by rescaling.
   
*Note: Cross-size or Cross-architecture merges (e.g. Qwen merged with Phi) are intentionally blocked as they will cause mathematical slice mismatch alignment (RuntimeError) during layer summation.*
