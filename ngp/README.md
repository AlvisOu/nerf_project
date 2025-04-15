# Instant-NGP NeRF setup

## Set up docker image
- Download .tar file from Drive
- Move the file into /ngp subdirectory
- Run `docker load -i instant-ngp-final.tar` to load the image

## To run training on sample fox dataset and save snapshot
Run `docker run --rm --gpus all -it \
  -v $(pwd):/project \
  --entrypoint bash \
  instant-ngp-final -c "cd /instant-ngp && python3 scripts/run.py \
    --scene /project/data/nerf/fox \
    --save_snapshot /project/fox_snapshot.msgpack \
    --n_steps 5000"`


