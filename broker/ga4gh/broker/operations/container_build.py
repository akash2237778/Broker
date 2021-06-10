
import docker

client = docker.from_env()

def createImage(path: str, tag: str, dockerfile: str):
    image = client.images.build(path="./clone", tag="akash", dockerfile="Dockerfile")
    print(image[0].short_id)



