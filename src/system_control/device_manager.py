"""
ماژول کنترل و مدیریت دستگاه‌ها (گوشی و کامپیوتر)
"""

import os
import subprocess
import platform
import psutil
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
import json
import requests
from pathlib import Path

from config.settings import settings


class DeviceManager:
    """مدیر کنترل دستگاه‌ها"""
    
    def __init__(self):
        self.system_info = self._get_system_info()
        self.permissions = self._check_permissions()
        
    def _get_system_info(self) -> Dict[str, Any]:
        """دریافت اطلاعات سیستم"""
        return {
            "platform": platform.system(),
            "platform_release": platform.release(),
            "platform_version": platform.version(),
            "architecture": platform.machine(),
            "hostname": platform.node(),
            "processor": platform.processor(),
            "ram": f"{round(psutil.virtual_memory().total / (1024.0 **3))} GB",
            "cpu_cores": psutil.cpu_count(),
            "cpu_usage": psutil.cpu_percent(),
            "disk_usage": psutil.disk_usage('/').percent if os.name != 'nt' else psutil.disk_usage('C:\\').percent
        }
    
    def _check_permissions(self) -> Dict[str, bool]:
        """بررسی مجوزهای دسترسی"""
        permissions = {
            "admin_access": self._has_admin_access(),
            "file_system": self._can_access_filesystem(),
            "network": self._can_access_network(),
            "processes": self._can_manage_processes(),
            "system_settings": self._can_modify_system_settings()
        }
        return permissions
    
    def _has_admin_access(self) -> bool:
        """بررسی دسترسی مدیریتی"""
        try:
            if platform.system() == "Windows":
                import ctypes
                return ctypes.windll.shell32.IsUserAnAdmin()
            else:
                return os.geteuid() == 0
        except:
            return False
    
    def _can_access_filesystem(self) -> bool:
        """بررسی دسترسی به فایل سیستم"""
        try:
            test_path = Path.home() / "test_access.tmp"
            test_path.touch()
            test_path.unlink()
            return True
        except:
            return False
    
    def _can_access_network(self) -> bool:
        """بررسی دسترسی به شبکه"""
        try:
            response = requests.get("https://www.google.com", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def _can_manage_processes(self) -> bool:
        """بررسی قابلیت مدیریت پروسه‌ها"""
        try:
            processes = psutil.pids()
            return len(processes) > 0
        except:
            return False
    
    def _can_modify_system_settings(self) -> bool:
        """بررسی قابلیت تغییر تنظیمات سیستم"""
        return self._has_admin_access()


class WindowsController(DeviceManager):
    """کنترلر ویندوز"""
    
    async def execute_command(self, command: str) -> Dict[str, Any]:
        """اجرای دستور در ویندوز"""
        try:
            result = subprocess.run(
                command, 
                shell=True, 
                capture_output=True, 
                text=True, 
                timeout=30
            )
            
            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr,
                "return_code": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Command timeout"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def manage_applications(self, action: str, app_name: str) -> Dict[str, Any]:
        """مدیریت اپلیکیشن‌ها"""
        commands = {
            "start": f"start {app_name}",
            "stop": f"taskkill /f /im {app_name}.exe",
            "restart": f"taskkill /f /im {app_name}.exe && start {app_name}"
        }
        
        if action in commands:
            return await self.execute_command(commands[action])
        else:
            return {"success": False, "error": "Invalid action"}
    
    async def system_control(self, action: str) -> Dict[str, Any]:
        """کنترل سیستم"""
        commands = {
            "shutdown": "shutdown /s /t 0",
            "restart": "shutdown /r /t 0",
            "sleep": "rundll32.exe powrprof.dll,SetSuspendState 0,1,0",
            "lock": "rundll32.exe user32.dll,LockWorkStation"
        }
        
        if action in commands:
            return await self.execute_command(commands[action])
        else:
            return {"success": False, "error": "Invalid system action"}
    
    async def get_installed_apps(self) -> List[Dict[str, Any]]:
        """دریافت لیست اپلیکیشن‌های نصب شده"""
        try:
            cmd = 'wmic product get name,version,vendor /format:csv'
            result = await self.execute_command(cmd)
            
            if result["success"]:
                apps = []
                lines = result["output"].strip().split('\n')[1:]  # حذف header
                
                for line in lines:
                    if line.strip():
                        parts = line.split(',')
                        if len(parts) >= 4:
                            apps.append({
                                "name": parts[1].strip(),
                                "version": parts[2].strip(),
                                "vendor": parts[3].strip()
                            })
                
                return apps
            else:
                return []
        except Exception as e:
            return []


class AndroidController(DeviceManager):
    """کنترلر اندروید (از طریق ADB)"""
    
    def __init__(self):
        super().__init__()
        self.adb_path = self._find_adb()
    
    def _find_adb(self) -> Optional[str]:
        """پیدا کردن مسیر ADB"""
        possible_paths = [
            "adb",
            "/usr/local/bin/adb",
            "/usr/bin/adb",
            "C:\\Program Files\\Android\\android-sdk\\platform-tools\\adb.exe"
        ]
        
        for path in possible_paths:
            try:
                subprocess.run([path, "version"], capture_output=True, timeout=5)
                return path
            except:
                continue
        
        return None
    
    async def execute_adb_command(self, command: str) -> Dict[str, Any]:
        """اجرای دستور ADB"""
        if not self.adb_path:
            return {"success": False, "error": "ADB not found"}
        
        try:
            full_command = f"{self.adb_path} {command}"
            result = subprocess.run(
                full_command.split(),
                capture_output=True,
                text=True,
                timeout=30
            )
            
            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr,
                "return_code": result.returncode
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_connected_devices(self) -> List[str]:
        """دریافت لیست دستگاه‌های متصل"""
        result = await self.execute_adb_command("devices")
        
        if result["success"]:
            lines = result["output"].strip().split('\n')[1:]  # حذف header
            devices = []
            
            for line in lines:
                if line.strip() and "device" in line:
                    device_id = line.split()[0]
                    devices.append(device_id)
            
            return devices
        else:
            return []
    
    async def install_app(self, apk_path: str, device_id: str = None) -> Dict[str, Any]:
        """نصب اپلیکیشن"""
        device_param = f"-s {device_id}" if device_id else ""
        command = f"{device_param} install {apk_path}"
        
        return await self.execute_adb_command(command)
    
    async def uninstall_app(self, package_name: str, device_id: str = None) -> Dict[str, Any]:
        """حذف اپلیکیشن"""
        device_param = f"-s {device_id}" if device_id else ""
        command = f"{device_param} uninstall {package_name}"
        
        return await self.execute_adb_command(command)
    
    async def start_app(self, package_name: str, activity: str = None, device_id: str = None) -> Dict[str, Any]:
        """شروع اپلیکیشن"""
        device_param = f"-s {device_id}" if device_id else ""
        
        if activity:
            command = f"{device_param} shell am start -n {package_name}/{activity}"
        else:
            command = f"{device_param} shell monkey -p {package_name} -c android.intent.category.LAUNCHER 1"
        
        return await self.execute_adb_command(command)
    
    async def stop_app(self, package_name: str, device_id: str = None) -> Dict[str, Any]:
        """توقف اپلیکیشن"""
        device_param = f"-s {device_id}" if device_id else ""
        command = f"{device_param} shell am force-stop {package_name}"
        
        return await self.execute_adb_command(command)
    
    async def get_installed_apps(self, device_id: str = None) -> List[Dict[str, Any]]:
        """دریافت لیست اپلیکیشن‌های نصب شده"""
        device_param = f"-s {device_id}" if device_id else ""
        command = f"{device_param} shell pm list packages -f"
        
        result = await self.execute_adb_command(command)
        
        if result["success"]:
            apps = []
            lines = result["output"].strip().split('\n')
            
            for line in lines:
                if line.startswith("package:"):
                    parts = line.split("=")
                    if len(parts) == 2:
                        package_name = parts[1].strip()
                        apps.append({
                            "package_name": package_name,
                            "path": parts[0].replace("package:", "")
                        })
            
            return apps
        else:
            return []
    
    async def take_screenshot(self, output_path: str, device_id: str = None) -> Dict[str, Any]:
        """گرفتن اسکرین‌شات"""
        device_param = f"-s {device_id}" if device_id else ""
        
        # گرفتن اسکرین‌شات در دستگاه
        screenshot_cmd = f"{device_param} shell screencap -p /sdcard/screenshot.png"
        result1 = await self.execute_adb_command(screenshot_cmd)
        
        if not result1["success"]:
            return result1
        
        # انتقال فایل به کامپیوتر
        pull_cmd = f"{device_param} pull /sdcard/screenshot.png {output_path}"
        result2 = await self.execute_adb_command(pull_cmd)
        
        # پاک کردن فایل از دستگاه
        cleanup_cmd = f"{device_param} shell rm /sdcard/screenshot.png"
        await self.execute_adb_command(cleanup_cmd)
        
        return result2
    
    async def send_text(self, text: str, device_id: str = None) -> Dict[str, Any]:
        """ارسال متن به دستگاه"""
        device_param = f"-s {device_id}" if device_id else ""
        # جایگزینی فاصله‌ها با %s برای ADB
        escaped_text = text.replace(" ", "%s")
        command = f"{device_param} shell input text {escaped_text}"
        
        return await self.execute_adb_command(command)
    
    async def simulate_tap(self, x: int, y: int, device_id: str = None) -> Dict[str, Any]:
        """شبیه‌سازی لمس صفحه"""
        device_param = f"-s {device_id}" if device_id else ""
        command = f"{device_param} shell input tap {x} {y}"
        
        return await self.execute_adb_command(command)
    
    async def simulate_swipe(self, x1: int, y1: int, x2: int, y2: int, duration: int = 300, device_id: str = None) -> Dict[str, Any]:
        """شبیه‌سازی کشیدن انگشت"""
        device_param = f"-s {device_id}" if device_id else ""
        command = f"{device_param} shell input swipe {x1} {y1} {x2} {y2} {duration}"
        
        return await self.execute_adb_command(command)


class UniversalDeviceController:
    """کنترلر جهانی برای تمام دستگاه‌ها"""
    
    def __init__(self):
        self.controllers = {}
        self._initialize_controllers()
    
    def _initialize_controllers(self):
        """راه‌اندازی کنترلرهای مختلف"""
        system = platform.system().lower()
        
        if system == "windows":
            self.controllers["windows"] = WindowsController()
        elif system in ["linux", "darwin"]:  # Linux or macOS
            self.controllers["unix"] = DeviceManager()
        
        # کنترلر اندروید همیشه در دسترس است
        self.controllers["android"] = AndroidController()
    
    async def execute_universal_command(self, command_type: str, **kwargs) -> Dict[str, Any]:
        """اجرای دستور جهانی"""
        
        if command_type == "system_info":
            return await self._get_all_system_info()
        
        elif command_type == "manage_app":
            return await self._manage_application(**kwargs)
        
        elif command_type == "system_control":
            return await self._control_system(**kwargs)
        
        elif command_type == "device_status":
            return await self._get_device_status()
        
        else:
            return {"success": False, "error": "Unknown command type"}
    
    async def _get_all_system_info(self) -> Dict[str, Any]:
        """دریافت اطلاعات تمام سیستم‌ها"""
        info = {}
        
        for name, controller in self.controllers.items():
            try:
                info[name] = controller.system_info
            except:
                info[name] = {"error": "Unable to get system info"}
        
        return {"success": True, "data": info}
    
    async def _manage_application(self, platform: str, action: str, app_name: str, **kwargs) -> Dict[str, Any]:
        """مدیریت اپلیکیشن در پلتفرم مشخص"""
        
        if platform == "windows" and "windows" in self.controllers:
            return await self.controllers["windows"].manage_applications(action, app_name)
        
        elif platform == "android" and "android" in self.controllers:
            if action == "start":
                return await self.controllers["android"].start_app(app_name, kwargs.get("activity"))
            elif action == "stop":
                return await self.controllers["android"].stop_app(app_name)
            elif action == "install":
                return await self.controllers["android"].install_app(app_name, kwargs.get("device_id"))
            elif action == "uninstall":
                return await self.controllers["android"].uninstall_app(app_name, kwargs.get("device_id"))
        
        return {"success": False, "error": f"Platform {platform} not supported or action {action} not available"}
    
    async def _control_system(self, platform: str, action: str, **kwargs) -> Dict[str, Any]:
        """کنترل سیستم"""
        
        if platform == "windows" and "windows" in self.controllers:
            return await self.controllers["windows"].system_control(action)
        
        return {"success": False, "error": f"System control not available for {platform}"}
    
    async def _get_device_status(self) -> Dict[str, Any]:
        """دریافت وضعیت تمام دستگاه‌ها"""
        status = {}
        
        # وضعیت سیستم اصلی
        status["main_system"] = {
            "cpu_usage": psutil.cpu_percent(),
            "memory_usage": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage('/').percent if os.name != 'nt' else psutil.disk_usage('C:\\').percent,
            "network_status": self.controllers.get("windows", DeviceManager())._can_access_network()
        }
        
        # وضعیت دستگاه‌های اندروید
        if "android" in self.controllers:
            android_devices = await self.controllers["android"].get_connected_devices()
            status["android_devices"] = {
                "connected_count": len(android_devices),
                "device_ids": android_devices
            }
        
        return {"success": True, "data": status}
