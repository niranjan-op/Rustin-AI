import os
import docker
from docker.errors import DockerException, ImageNotFound, NotFound

CONTAINER_NAME = "agent-sandbox"
IMAGE_TAG = "agent-sandbox:latest"

def get_docker_client():
    try:
        return docker.from_env()
    except DockerException as e:
        raise RuntimeError(
            "Could not connect to the Docker daemon. "
            "Please ensure Docker Desktop is installed and running on your system."
        ) from e

def build_sandbox_image(client):
    try:
        client.images.get(IMAGE_TAG)
        print(f"Docker image '{IMAGE_TAG}' already exists.")
    except ImageNotFound:
        print(f"Building Docker image '{IMAGE_TAG}' from Dockerfile...")
        # Path is current directory where Dockerfile is created
        client.images.build(path=".", tag=IMAGE_TAG, rm=True)
        print("Docker image built successfully.")

def get_or_create_sandbox_container():
    client = get_docker_client()
    build_sandbox_image(client)
    
    try:
        # Check if container already exists
        container = client.containers.get(CONTAINER_NAME)
        
        # If it exists but is stopped, start it
        if container.status != "running":
            print(f"Starting stopped container: {CONTAINER_NAME}")
            container.start()
            
        return container
    except NotFound:
        print(f"Creating and starting new container: {CONTAINER_NAME}")
        # Run a container that stays alive using tail -f /dev/null
        container = client.containers.run(
            IMAGE_TAG,
            name=CONTAINER_NAME,
            detach=True,
            restart_policy={"Name": "unless-stopped"},
            # Security limits (optional but recommended)
            mem_limit="512m",
            nano_cpus=1000000000  # limit to 1 CPU core
        )
        return container

def execute_command_in_sandbox(command: str) -> str:
    """
    Executes a bash command inside the sandbox container and returns the stdout/stderr.
    """
    try:
        container = get_or_create_sandbox_container()
        
        # Run the command inside the container
        # We run it under bash to support piping and shell built-ins
        exec_result = container.exec_run(
            cmd=["/bin/bash", "-c", command],
            workdir="/workspace"
        )
        
        output = exec_result.output.decode("utf-8", errors="replace")
        
        # Prefix the output with a status message if the command failed
        if exec_result.exit_code != 0:
            return f"[Command Failed - Exit Code {exec_result.exit_code}]\n{output}"
            
        return output
    except Exception as e:
        return f"Error executing command in sandbox: {str(e)}"

def write_file_to_sandbox(file_path: str, content: str) -> str:
    """
    Writes text content to a file inside the sandbox container.
    """
    try:
        container = get_or_create_sandbox_container()
        
        import base64
        encoded_content = base64.b64encode(content.encode('utf-8')).decode('utf-8')
        
        # Run a bash command to decode and write the file
        command = f"echo '{encoded_content}' | base64 -d > {file_path}"
        exec_result = container.exec_run(
            cmd=["/bin/bash", "-c", command],
            workdir="/workspace"
        )
        
        if exec_result.exit_code != 0:
            return f"[File Write Failed - Exit Code {exec_result.exit_code}]\n{exec_result.output.decode('utf-8', errors='replace')}"
            
        return f"Successfully wrote to {file_path}"
    except Exception as e:
        return f"Error writing file to sandbox: {str(e)}"
