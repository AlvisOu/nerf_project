FROM nvidia/cuda:12.2.0-devel-ubuntu22.04

# Install system dependencies
RUN apt update && apt install -y \
    build-essential cmake git curl \
    libglfw3-dev libglew-dev libx11-dev libxi-dev \
    libxxf86vm-dev libxrandr-dev libxinerama-dev libxcursor-dev \
    python3 python3-pip

# Clone Instant-NGP
RUN git clone --recursive https://github.com/NVlabs/instant-ngp.git /instant-ngp
WORKDIR /instant-ngp

# Install Python dependencies
RUN pip3 install numpy imageio tqdm matplotlib configargparse commentjson scipy

# Build Instant-NGP (with compute capability 7.5 for T4)
RUN cmake . -B build -DCMAKE_CUDA_ARCHITECTURES="75" && \
    cmake --build build --config RelWithDebInfo -j $(nproc)

# Copy your Python scripts
COPY renderer.py /instant-ngp/scripts/
COPY block_manager.py /instant-ngp/scripts/

# Set PYTHONPATH so imports like common.py work
ENV PYTHONPATH=/instant-ngp/scripts:$PYTHONPATH

# Default command to run renderer
ENTRYPOINT ["python3", "/instant-ngp/scripts/renderer.py"]
