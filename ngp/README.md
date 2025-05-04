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

To use scripts/run.py to load msgpack AND display it 
Run `python3 scripts/run.py data/nerf/fox --load_snapshot=fox_snapshot.msgpack --gui`
the --gui indicates that we shoould display the model.

BELOW ARE ALL BASH
To open GUI (this is the vcxsrv):

First, open Xlaunch on your computer
Second, on the configuration, set Xlaunch display no. to 0
Third:Run in /nerf_project: `docker run --gpus all -it -v $(pwd):/workspace -e DISPLAY=host.docker.internal:0 instant-ngp-final`

To create and open a new docker container:
`docker run --gpus all -it -v $(pwd -W):/project -e DISPLAY=host.docker.internal:0 --entrypoint bash instant-ngp-final`

To list existing containers:
`docker ps -a`

To open an existing container:
`docker start -ai <container_name>`
currently: 
-Name: stupefied_pascal
-ID:   df80ac9bce2f

To exit a container:
`exit`

To copy files from project to docker:
`docker cp <local_file_path> <docker_container_id>:/<docker_file_path>`
e.g
`docker cp data/chairs/close df80ac9bce2f:/instant-ngp/data/chairs`

ACTUAL EXECUTION:
In /instant-ngp directory of docker:
python3 scripts/renderer.py --snapshots msgpacks/room_2 --gui

room_2 contains the actual files corresponding to the database.


Portals:
slippers_outside -> chairs_multi portal at (x: 1.32, z: 3.2)
chairs_multi -> slippers_outside portal at (x: 1.379, z: -0.4)

FOR REGULAR WORKFLOW:
0. Open docker desttop 

1. Open XLaunch
    - set display no. to 0
    - Run `docker run --gpus all -it -v $(pwd):/workspace -e DISPLAY=host.docker.internal:0 instant-ngp-final`

2. Open docker in terminal 1
    `docker start -ai stupefied_pascal`

3. Copy the edited files into docker:
    `docker cp block_manager.py df80ac9bce2f:/instant-ngp/scripts`
    `docker cp renderer.py df80ac9bce2f:/instant-ngp/scripts`

4. Run the program in docker:
    `python3 scripts/renderer.py --snapshots msgpacks/room_2 --gui`