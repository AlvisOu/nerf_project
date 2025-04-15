# NeRF virtual tour project

## Tentative architecture
```
[ User ] → clicks → triggers loading of relevant NeRF blocks

[ Scene Graph ]
   └── Nodes = FastNeRF-trained blocks (small, independent)
   └── Edges = Transitions with appearance alignment

[ Runtime ]
   └── Uses Block-NeRF's visibility filtering & blending
   └── CUDA acceleration via FastNeRF (tiny-cuda-nn)
   └── Updates or adds blocks without retraining global model

[ Interface ]
   └── Web-based UI: supports click-to-teleport, dynamic loading
```
