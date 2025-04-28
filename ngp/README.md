# Instant-NGP NeRF setup
Run all below commands in ngp/

## To set up docker image
Run `docker build -t instant-ngp-final .`

## To run training on sample fox dataset and save snapshot
Run `docker run --rm --gpus all -it -v $(pwd -C):/project --entrypoint bash instant-ngp-final -c "cd /instant-ngp && python3 scripts/run.py --scene /project/data/nerf/fox --save_snapshot /project/fox_snapshot.msgpack --n_steps 5000"`

FOR SUNNY (use -W in $(pwd -W)):
Run 'docker run --rm --gpus all -it -v $(pwd -W):/project --entrypoint bash instant-ngp-final -c "cd /instant-ngp && python3 scripts/run.py --scene /project/data/chairs/multi --save_snapshot /project/chairs_multi_snapshot.msgpack --n_steps 5000"'


NOTE, TO SEE GUI, DOWNLOAD FROM:

https://sourceforge.net/projects/vcxsrv/

THIS IS WHAT WILL BE USED FOR DISPLAY

## To train and view scene
RUN `.\instant-ngp data/nerf/fox`

## To load msgpack
Run `.\instant-ngp.exe data/nerf/fox --load_snapshot=fox_snapshot.msgpack`
Make sure the .msgpack file is located on the same level as the data/ folder

To use scripts/run.py, 
Run `python3 scripts/run.py data/nerf/fox --load_snapshot=fox_snapshot.msgpack`

BELOW ARE ALL BASH
To open GUI (this is the vcxsrv):
Run in /nerf_project: `docker run --gpus all -it -v $(pwd):/workspace -e DISPLAY=host.docker.internal:0 instant-ngp-final`

To open docker file path:
`docker run --gpus all -it -v $(pwd -W):/project -e DISPLAY=host.docker.internal:0 --entrypoint bash instant-ngp-final`

To copy files from project to docker:
`docker cp <local_file_path> <docker_container_id>:/<docker_file_path>`
e.g
`docker cp data/chairs/close 59f726f0614f:/instant-ngp/data/chairs`
