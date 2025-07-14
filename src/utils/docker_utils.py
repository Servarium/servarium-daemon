import docker

def docker_action(container_name: str, action: str) -> dict:
    try:
        client = docker.from_env()
        container = client.containers.get(container_name)

        if action == "start":
            container.start()
            return {"status": "success", "message": f"Container {container_name} started."}
        elif action == "stop":
            container.stop()
            return {"status": "success", "message": f"Container {container_name} stopped."}
        elif action == "restart":
            container.restart()
            return {"status": "success", "message": f"Container {container_name} restarted."}
        else:
            return {"status": "error", "message": "Invalid action."}
    except docker.errors.NotFound:
        return {"status": "error", "message": f"Container {container_name} not found."}
    except Exception as e:
        return {"status": "error", "message": str(e)}


