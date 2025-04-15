FROM nvidia/cuda:12.2.0-devel-ubuntu22.04

# Install system dependencies
RUN apt update && apt install -y \
    build-essential cmake git curl \
    libglfw3-dev libglew-dev libx11-dev libxi-dev \
    libxxf86vm-dev libxrandr-dev libxinerama-dev libxcursor-dev \
    python3 python3-pip

# Clone instant-ngp repo
RUN git clone --recursive https://github.com/NVlabs/instant-ngp.git /instant-ngp
WORKDIR /instant-ngp

# Install Python packages
RUN pip3 install numpy imageio tqdm matplotlib configargparse commentjson scipy

# Build for T4 GPU (compute 7.5)
RUN cmake . -B build -DCMAKE_CUDA_ARCHITECTURES="75" && \
    cmake --build build --config RelWithDebInfo -j $(nproc)

ENTRYPOINT ["/instant-ngp/build/instant-ngp"]

