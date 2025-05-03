# NeRF virtual tour project

## To build Docker in stitch_nerf
Run `docker build -t instant-ngp-renderer .`

## To run
`
docker run --gpus all -it `
  -v "$(pwd)/../ngp/data:/instant-ngp/data" `
  -e DISPLAY=host.docker.internal:0 `
  instant-ngp-renderer `
  --gui --snapshots /instant-ngp/data/chairs/chairs_multi
`