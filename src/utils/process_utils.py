import psutil

def terminate_process(pid: int) -> dict:
    try:
        process = psutil.Process(pid)
        process.terminate()
        return {"status": "success", "message": f"Process {pid} terminated."}
    except psutil.NoSuchProcess:
        return {"status": "error", "message": f"Process {pid} not found."}
    except psutil.AccessDenied:
        return {"status": "error", "message": f"Access denied to terminate process {pid}."}
    except Exception as e:
        return {"status": "error", "message": str(e)}


