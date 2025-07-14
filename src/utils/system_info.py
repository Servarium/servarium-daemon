import platform
import psutil
import uuid
import subprocess

def get_system_info():
    info = {
        "os_name": platform.system(),
        "os_version": platform.version(),
        "distribution": platform.freedesktop_os_release().get("PRETTY_NAME", "N/A") if hasattr(platform, "freedesktop_os_release") else "N/A",
        "processor_name": platform.processor(),
        "processor_cores": psutil.cpu_count(logical=False),
        "processor_frequency": psutil.cpu_freq().current if psutil.cpu_freq() else "N/A",
        "total_memory_gb": round(psutil.virtual_memory().total / (1024**3), 2),
        "serial_number": get_motherboard_serial_number(),
        "gpu_name": get_gpu_name()
    }
    return info

def get_motherboard_serial_number():
    try:
        if platform.system() == "Linux":
            # Try dmidecode first
            result = subprocess.run(["sudo", "dmidecode", "-s", "baseboard-serial-number"], capture_output=True, text=True)
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
            # Fallback to /sys/class/dmi/id/board_serial
            with open("/sys/class/dmi/id/board_serial", "r") as f:
                return f.read().strip()
        elif platform.system() == "Windows":
            result = subprocess.run(["wmic", "baseboard", "get", "SerialNumber"], capture_output=True, text=True)
            lines = result.stdout.strip().split("\n")
            if len(lines) > 1:
                return lines[1].strip()
    except Exception:
        pass
    return "N/A"

def get_gpu_name():
    try:
        if platform.system() == "Linux":
            result = subprocess.run(["lspci", "-vnn"], capture_output=True, text=True)
            for line in result.stdout.splitlines():
                if "VGA compatible controller" in line or "3D controller" in line:
                    # Extract name from the line, often after a colon or bracket
                    if ":" in line:
                        return line.split(":")[-1].split("(")[0].strip()
                    else:
                        return line.strip()
        elif platform.system() == "Windows":
            result = subprocess.run(["wmic", "path", "Win32_VideoController", "get", "Name"], capture_output=True, text=True)
            lines = result.stdout.strip().split("\n")
            if len(lines) > 1:
                return lines[1].strip()
    except Exception:
        pass
    return "N/A"

def get_available_components():
    components = {
        "cpu": True,
        "ram": True,
        "disks": True,
        "network": True,
        "processes": True,
        "uptime": True,
        "docker": False # Assume false, check later
    }
    try:
        import docker
        client = docker.from_env()
        client.ping()
        components["docker"] = True
    except Exception:
        pass
    return components

if __name__ == "__main__":
    print("System Info:", get_system_info())
    print("Available Components:", get_available_components())


