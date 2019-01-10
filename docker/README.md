Files used to build the dokcer image.
When building the docker, every file in this folder should be included in the build context.

- Dockerfile

    Dockerfile of the docker.

- startup.sh

    start up script for the container (Note: Not the GCP VM).
    It will start cms services based on env variable CMS_INSTANCE_TYPE.
