# Instant-NGP NeRF setup
Run all below commands in ngp/

## To set up docker image
Run `docker build -t instant-ngp-final .`

## To run training on sample fox dataset and save snapshot
Run `docker run --rm --gpus all -it -v $(pwd -C):/project --entrypoint bash instant-ngp-final -c "cd /instant-ngp && python3 scripts/run.py --scene /project/data/nerf/fox --save_snapshot /project/fox_snapshot.msgpack --n_steps 5000"`

FOR SUNNY (use -W in $(pwd -W)):
Run 'docker run --rm --gpus all -it -v $(pwd -W):/project --entrypoint bash instant-ngp-final -c "cd /instant-ngp && python3 scripts/run.py --scene /project/data/chairs/multi --save_snapshot /project/chairs_multi_snapshot.msgpack --n_steps 5000"'

## To load msgpack and view rendered scene
Run `.\instant-ngp.exe data/nerf/fox --load_snapshot=fox_snapshot.msgpack`
Make sure the .msgpack file is located on the same level as the data/ folder
