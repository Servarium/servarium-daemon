import psutil
import docker
import json
import uuid
import datetime
import platform
import socket
import subprocess
import os
from typing import Dict, List, Any, Optional
from src.utils.system_info import get_system_info, get_available_components

class MetricsCollector:
    def __init__(self):
        self.docker_client = None
        self.available_components = self._detect_available_components()
    
    def _detect_available_components(self) -> List[str]:
        """Определяет доступные компоненты для мониторинга"""
        components = get_available_components()
        if "docker" in components and self.docker_client is None:
            try:
                self.docker_client = docker.from_env()
                self.docker_client.ping()
            except Exception:
                self.docker_client = None
        return components
    
    def get_available_components(self) -> List[str]:
        """Возвращает список доступных компонентов"""
        return self.available_components

    def collect_system_info(self) -> Dict[str, Any]:
        """Собирает информацию о системе"""
        return get_system_info()
    
    def collect_cpu_metrics(self) -> Dict[str, Any]:
        """Собирает метрики CPU"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            cpu_freq = psutil.cpu_freq()
            
            temperature = None
            try:
                if hasattr(psutil, 'sensors_temperatures'):
                    temps = psutil.sensors_temperatures()
                    if temps:
                        for name, entries in temps.items():
                            if entries:
                                temperature = entries[0].current
                                break
            except Exception:
                pass
            
            return {
                'usage': cpu_percent,
                'temperature': temperature,
                'count': cpu_count,
                'frequency': {
                    'current': cpu_freq.current if cpu_freq else None,
                    'min': cpu_freq.min if cpu_freq else None,
                    'max': cpu_freq.max if cpu_freq else None
                } if cpu_freq else None,
                'per_cpu': psutil.cpu_percent(percpu=True)
            }
        except Exception as e:
            return {'error': str(e)}
    
    def collect_memory_metrics(self) -> Dict[str, Any]:
        """Собирает метрики памяти"""
        try:
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            return {
                'total': memory.total,
                'available': memory.available,
                'used': memory.used,
                'percentage': memory.percent,
                'free': memory.free,
                'swap': {
                    'total': swap.total,
                    'used': swap.used,
                    'free': swap.free,
                    'percentage': swap.percent
                }
            }
        except Exception as e:
            return {'error': str(e)}
    
    def collect_disk_metrics(self) -> Dict[str, Any]:
        """Собирает метрики дисков"""
        try:
            disks = []
            disk_partitions = psutil.disk_partitions()
            
            for partition in disk_partitions:
                try:
                    disk_usage = psutil.disk_usage(partition.mountpoint)
                    disk_io = psutil.disk_io_counters(perdisk=True)
                    
                    disk_info = {
                        'device': partition.device,
                        'mountpoint': partition.mountpoint,
                        'fstype': partition.fstype,
                        'total': disk_usage.total,
                        'used': disk_usage.used,
                        'free': disk_usage.free,
                        'percentage': (disk_usage.used / disk_usage.total) * 100 if disk_usage.total > 0 else 0
                    }
                    
                    device_name = partition.device.split('/')[-1]
                    if disk_io and device_name in disk_io:
                        io_stats = disk_io[device_name]
                        disk_info['io'] = {
                            'read_bytes': io_stats.read_bytes,
                            'write_bytes': io_stats.write_bytes,
                            'read_count': io_stats.read_count,
                            'write_count': io_stats.write_count
                        }
                    
                    disks.append(disk_info)
                except Exception:
                    continue
            
            return {'disks': disks}
        except Exception as e:
            return {'error': str(e)}
    
    def collect_network_metrics(self) -> Dict[str, Any]:
        """Собирает сетевые метрики"""
        try:
            network_io = psutil.net_io_counters(pernic=True)
            network_interfaces = []
            
            for interface_name, io_stats in network_io.items():
                addresses = psutil.net_if_addrs().get(interface_name, [])
                local_addresses = []
                
                for addr in addresses:
                    if addr.family == socket.AF_INET:  # IPv4
                        local_addresses.append({
                            'type': 'IPv4',
                            'address': addr.address,
                            'netmask': addr.netmask,
                            'broadcast': addr.broadcast
                        })
                    elif addr.family == socket.AF_INET6:  # IPv6
                        local_addresses.append({
                            'type': 'IPv6',
                            'address': addr.address,
                            'netmask': addr.netmask
                        })
                
                interface_info = {
                    'name': interface_name,
                    'bytes_sent': io_stats.bytes_sent,
                    'bytes_recv': io_stats.bytes_recv,
                    'packets_sent': io_stats.packets_sent,
                    'packets_recv': io_stats.packets_recv,
                    'errin': io_stats.errin,
                    'errout': io_stats.errout,
                    'dropin': io_stats.dropin,
                    'dropout': io_stats.dropout,
                    'addresses': local_addresses
                }
                
                network_interfaces.append(interface_info)
            
            external_ip = None
            try:
                import requests
                response = requests.get('https://api.ipify.org', timeout=5)
                external_ip = response.text
            except Exception:
                pass
            
            return {
                'interfaces': network_interfaces,
                'external_ip': external_ip
            }
        except Exception as e:
            return {'error': str(e)}
    
    def collect_processes_metrics(self) -> Dict[str, Any]:
        """Собирает метрики процессов"""
        try:
            processes_cpu = []
            processes_memory = []
            
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info', 'status', 'cmdline']):
                try:
                    proc_info = proc.info
                    memory_mb = proc_info['memory_info'].rss / 1024 / 1024  # Конвертируем в MB
                    cpu_percent = proc_info['cpu_percent'] or 0
                    command = ' '.join(proc_info['cmdline']) if proc_info['cmdline'] else proc_info['name']
                    
                    process_data = {
                        'pid': proc_info['pid'],
                        'name': proc_info['name'],
                        'command': command,
                        'cpu_percent': cpu_percent,
                        'memory_mb': round(memory_mb, 2),
                        'status': proc_info['status']
                    }
                    
                    processes_cpu.append(process_data)
                    processes_memory.append(process_data)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            processes_cpu.sort(key=lambda x: x['cpu_percent'], reverse=True)
            processes_memory.sort(key=lambda x: x['memory_mb'], reverse=True)
            
            return {
                'top_cpu': processes_cpu[:5],
                'top_memory': processes_memory[:5]
            }
        except Exception as e:
            return {'error': str(e)}
    
    def collect_uptime_metrics(self) -> Dict[str, Any]:
        """Собирает метрики времени работы системы"""
        try:
            boot_time = psutil.boot_time()
            uptime_seconds = datetime.datetime.now().timestamp() - boot_time
            
            days = int(uptime_seconds // 86400)
            hours = int((uptime_seconds % 86400) // 3600)
            minutes = int((uptime_seconds % 3600) // 60)
            
            return {
                'boot_time': datetime.datetime.fromtimestamp(boot_time).isoformat(),
                'uptime_seconds': int(uptime_seconds),
                'uptime_formatted': f"{days}д {hours}ч {minutes}м",
                'load_average': os.getloadavg() if hasattr(os, 'getloadavg') else None
            }
        except Exception as e:
            return {'error': str(e)}
    
    def collect_docker_metrics(self) -> Dict[str, Any]:
        """Собирает метрики Docker контейнеров"""
        if not self.docker_client:
            return {'error': 'Docker not available'}
        
        try:
            containers = []
            
            for container in self.docker_client.containers.list(all=True):
                try:
                    stats = None
                    if container.status == 'running':
                        try:
                            stats = container.stats(stream=False)
                        except Exception:
                            pass
                    
                    container_info = {
                        'id': container.short_id,
                        'name': container.name,
                        'image': container.image.tags[0] if container.image.tags else container.image.id[:12],
                        'status': container.status,
                        'created': container.attrs['Created'],
                        'ports': container.ports if hasattr(container, 'ports') else {}
                    }
                    
                    if stats:
                        cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - stats['precpu_stats']['cpu_usage']['total_usage']
                        system_delta = stats['cpu_stats']['system_cpu_usage'] - stats['precpu_stats']['system_cpu_usage']
                        cpu_percent = 0
                        if system_delta > 0:
                            cpu_percent = (cpu_delta / system_delta) * len(stats['cpu_stats']['cpu_usage']['percpu_usage']) * 100
                        
                        memory_usage = stats['memory_stats'].get('usage', 0)
                        memory_limit = stats['memory_stats'].get('limit', 0)
                        memory_percent = (memory_usage / memory_limit) * 100 if memory_limit > 0 else 0
                        
                        container_info['resources'] = {
                            'cpu_percent': round(cpu_percent, 2),
                            'memory_usage': memory_usage,
                            'memory_limit': memory_limit,
                            'memory_percent': round(memory_percent, 2)
                        }
                    
                    containers.append(container_info)
                except Exception:
                    continue
            
            return {
                'containers': containers,
                'total_containers': len(containers),
                'running_containers': len([c for c in containers if c['status'] == 'running'])
            }
        except Exception as e:
            return {'error': str(e)}
    
    def collect_all_metrics(self) -> Dict[str, Any]:
        """Собирает все доступные метрики"""
        metrics = {}
        
        for component in self.available_components:
            if component == 'cpu':
                metrics['cpu'] = self.collect_cpu_metrics()
            elif component == 'memory':
                metrics['memory'] = self.collect_memory_metrics()
            elif component == 'disks': # Изменено с 'disk' на 'disks'
                metrics['disks'] = self.collect_disk_metrics()
            elif component == 'network':
                metrics['network'] = self.collect_network_metrics()
            elif component == 'processes':
                metrics['processes'] = self.collect_processes_metrics()
            elif component == 'uptime':
                metrics['uptime'] = self.collect_uptime_metrics()
            elif component == 'docker':
                metrics['docker'] = self.collect_docker_metrics()
        
        metrics['system_info'] = self.collect_system_info() # Добавлено

        return metrics
    
    def generate_unique_key(self) -> str:
        """Генерирует уникальный ключ для агента"""
        return str(uuid.uuid4())


