"""
ماژول مدیریت امنیت و حریم خصوصی
شامل ردیاب، پاک‌کننده آثار، تشخیص نفوذ و حالت مخفی
"""

import asyncio
import os
import shutil
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging
import platform
import psutil
import re

from config.settings import settings

# پیکربندی لاگینگ
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class PrivacyProtector:
    """مدیریت حریم خصوصی و پاکسازی آثار"""
    
    def __init__(self):
        self.browsing_history_paths = self._get_browsing_history_paths()
        self.temp_dirs = self._get_temp_directories()
        self.privacy_log = []
    
    def _get_browsing_history_paths(self) -> List[str]:
        """دریافت مسیرهای تاریخچه مرورگرها"""
        paths = []
        home = os.path.expanduser("~ ")
        
        if platform.system() == "Windows":
            app_data = os.getenv("LOCALAPPDATA")
            if app_data:
                paths.append(os.path.join(app_data, "Google\Chrome\User Data\Default\History"))
                paths.append(os.path.join(app_data, "Microsoft\Edge\User Data\Default\History"))
        elif platform.system() == "Darwin":  # macOS
            paths.append(os.path.join(home, "Library/Application Support/Google/Chrome/Default/History"))
            paths.append(os.path.join(home, "Library/Application Support/Firefox/Profiles/*/places.sqlite"))
        else:  # Linux
            paths.append(os.path.join(home, ".config/google-chrome/Default/History"))
            paths.append(os.path.join(home, ".mozilla/firefox/*/places.sqlite"))
            paths.append(os.path.join(home, ".cache/mozilla/firefox/*/Cache"))
            paths.append(os.path.join(home, ".cache/google-chrome/Default/Cache"))
            
        return [p for p in paths if os.path.exists(p)]
    
    def _get_temp_directories(self) -> List[str]:
        """دریافت مسیرهای دایرکتوری‌های موقت"""
        temp_dirs = [
            os.path.join(os.path.expanduser("~ "), ".cache"),
            os.path.join(os.path.expanduser("~ "), ".local/share/Trash"), # Linux Trash
            "/tmp"
        ]
        if platform.system() == "Windows":
            temp_dirs.append(os.getenv("TEMP"))
            temp_dirs.append(os.getenv("TMP"))
        elif platform.system() == "Darwin":
            temp_dirs.append("/private/tmp")
            temp_dirs.append("/private/var/folders")
            
        return [d for d in temp_dirs if d and os.path.exists(d)]
    
    async def clear_browsing_history(self) -> Dict[str, Any]:
        """پاکسازی تاریخچه مرورگرها"""
        cleaned_files = []
        errors = []
        
        for path in self.browsing_history_paths:
            try:
                if os.path.isfile(path):
                    os.remove(path)
                    cleaned_files.append(path)
                    logger.info(f"Cleared browsing history file: {path}")
                elif os.path.isdir(path):
                    shutil.rmtree(path)
                    cleaned_files.append(path)
                    logger.info(f"Cleared browsing history directory: {path}")
            except Exception as e:
                errors.append(f"Error clearing {path}: {e}")
                logger.error(f"Error clearing browsing history: {e}")
        
        self.privacy_log.append({
            "action": "clear_browsing_history",
            "timestamp": datetime.now().isoformat(),
            "cleaned_files": cleaned_files,
            "errors": errors
        })
        
        return {"success": not errors, "cleaned_files": cleaned_files, "errors": errors}
    
    async def clear_temp_files(self) -> Dict[str, Any]:
        """پاکسازی فایل‌های موقت و کش"""
        cleaned_items = []
        errors = []
        
        for d in self.temp_dirs:
            for item in os.listdir(d):
                item_path = os.path.join(d, item)
                try:
                    if os.path.isfile(item_path):
                        os.remove(item_path)
                        cleaned_items.append(item_path)
                    elif os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                        cleaned_items.append(item_path)
                except Exception as e:
                    errors.append(f"Error clearing {item_path}: {e}")
                    logger.error(f"Error clearing temp item: {e}")
        
        self.privacy_log.append({
            "action": "clear_temp_files",
            "timestamp": datetime.now().isoformat(),
            "cleaned_items": cleaned_items,
            "errors": errors
        })
        
        return {"success": not errors, "cleaned_items": cleaned_items, "errors": errors}
    
    async def activate_stealth_mode(self) -> Dict[str, Any]:
        """فعال کردن حالت مخفی (شبیه‌سازی)"""
        # در یک پیاده‌سازی واقعی، این شامل پروکسی، VPN، تغییر User-Agent و غیره می‌شود
        logger.info("Stealth mode activated. All subsequent web activities will attempt to be untraceable.")
        self.privacy_log.append({
            "action": "activate_stealth_mode",
            "timestamp": datetime.now().isoformat(),
            "status": "activated"
        })
        return {"success": True, "message": "Stealth mode activated. (Simulated)"}
    
    async def deactivate_stealth_mode(self) -> Dict[str, Any]:
        """غیرفعال کردن حالت مخفی"""
        logger.info("Stealth mode deactivated.")
        self.privacy_log.append({
            "action": "deactivate_stealth_mode",
            "timestamp": datetime.now().isoformat(),
            "status": "deactivated"
        })
        return {"success": True, "message": "Stealth mode deactivated. (Simulated)"}
    
    def get_privacy_log(self, limit: int = 50) -> List[Dict[str, Any]]:
        """دریافت لاگ حریم خصوصی"""
        return self.privacy_log[-limit:]


class IntrusionDetector:
    """تشخیص نفوذ و ردیابی"""
    
    def __init__(self):
        self.monitoring_active = False
        self.intrusion_alerts = []
        self.known_network_devices = self._get_known_network_devices()
        self.baseline_processes = self._get_baseline_processes()
    
    def _get_known_network_devices(self) -> List[str]:
        """دریافت لیست دستگاه‌های شبکه شناخته شده (شبیه‌سازی)"""
        # در یک پیاده‌سازی واقعی، این لیست باید از طریق اسکن شبکه و تأیید کاربر ایجاد شود
        return ["192.168.1.1", "192.168.1.100", "my_router_mac"]
    
    def _get_baseline_processes(self) -> List[str]:
        """دریافت لیست فرآیندهای پایه سیستم"""
        return [p.name() for p in psutil.process_iter()]
    
    async def start_monitoring(self) -> Dict[str, Any]:
        """شروع نظارت بر سیستم"""
        self.monitoring_active = True
        logger.info("Intrusion detection monitoring started.")
        return {"success": True, "message": "Monitoring started"}
    
    async def stop_monitoring(self) -> Dict[str, Any]:
        """توقف نظارت بر سیستم"""
        self.monitoring_active = False
        logger.info("Intrusion detection monitoring stopped.")
        return {"success": True, "message": "Monitoring stopped"}
    
    async def check_for_intrusions(self) -> Dict[str, Any]:
        """بررسی نفوذها و فعالیت‌های مشکوک"""
        if not self.monitoring_active:
            return {"success": False, "error": "Monitoring is not active"}
        
        alerts = []
        
        # 1. بررسی فرآیندهای مشکوک
        new_processes = self._detect_new_processes()
        if new_processes:
            alerts.append({
                "type": "suspicious_process",
                "description": f"New unknown processes detected: {new_processes}",
                "severity": "HIGH",
                "timestamp": datetime.now().isoformat()
            })
            
        # 2. بررسی اتصالات شبکه مشکوک
        suspicious_connections = self._detect_suspicious_network_connections()
        if suspicious_connections:
            alerts.append({
                "type": "suspicious_network_connection",
                "description": f"Unknown network connections detected: {suspicious_connections}",
                "severity": "MEDIUM",
                "timestamp": datetime.now().isoformat()
            })
            
        # 3. بررسی تغییرات فایل‌های سیستمی حیاتی (شبیه‌سازی)
        if random.random() < 0.01: # 1% احتمال برای تست
            alerts.append({
                "type": "critical_file_change",
                "description": "Potential unauthorized modification of critical system files",
                "severity": "CRITICAL",
                "timestamp": datetime.now().isoformat()
            })
        
        if alerts:
            self.intrusion_alerts.extend(alerts)
            logger.warning(f"Intrusion alerts detected: {alerts}")
            return {"success": True, "alerts": alerts, "status": "INTRUSION_DETECTED"}
        else:
            return {"success": True, "alerts": [], "status": "CLEAN"}
    
    def _detect_new_processes(self) -> List[str]:
        """تشخیص فرآیندهای جدید و ناشناخته"""
        current_processes = [p.name() for p in psutil.process_iter()]
        new_processes = list(set(current_processes) - set(self.baseline_processes))
        return new_processes
    
    def _detect_suspicious_network_connections(self) -> List[Dict[str, Any]]:
        """تشخیص اتصالات شبکه مشکوک"""
        suspicious = []
        for conn in psutil.net_connections(kind=\'inet\'):
            if conn.raddr and conn.status == psutil.CONN_ESTABLISHED:
                remote_ip = conn.raddr.ip
                if remote_ip not in self.known_network_devices and not remote_ip.startswith("127."):
                    suspicious.append({
                        "local_address": f"{conn.laddr.ip}:{conn.laddr.port}",
                        "remote_address": f"{conn.raddr.ip}:{conn.raddr.port}",
                        "status": conn.status,
                        "pid": conn.pid
                    })
        return suspicious
    
    async def trace_attack_source(self, ip_address: str) -> Dict[str, Any]:
        """ردیابی منبع حمله بر اساس IP (شبیه‌سازی)"""
        # در یک پیاده‌سازی واقعی، این شامل استفاده از سرویس‌های GeoIP و تحلیل لاگ‌ها می‌شود
        logger.info(f"Attempting to trace IP: {ip_address}")
        
        if ip_address == "192.168.1.10": # مثال برای IP مهاجم
            return {
                "success": True,
                "ip_address": ip_address,
                "location": "Unknown (Internal Network)",
                "isp": "Local Network",
                "threat_level": "HIGH",
                "details": "Potential internal network scan or attack attempt.",
                "timestamp": datetime.now().isoformat()
            }
        elif ip_address == "203.0.113.45": # مثال برای IP خارجی
            return {
                "success": True,
                "ip_address": ip_address,
                "location": "Country: China, City: Beijing",
                "isp": "China Telecom",
                "threat_level": "MEDIUM",
                "details": "External connection from a known suspicious region.",
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "success": True,
                "ip_address": ip_address,
                "location": "Unknown",
                "isp": "Unknown",
                "threat_level": "LOW",
                "details": "Could not determine specific source details.",
                "timestamp": datetime.now().isoformat()
            }
    
    def get_intrusion_alerts(self, limit: int = 50) -> List[Dict[str, Any]]:
        """دریافت هشدارهای نفوذ"""
        return self.intrusion_alerts[-limit:]


class SecurityManager:
    """مدیر اصلی امنیت و حریم خصوصی"""
    
    def __init__(self):
        self.privacy_protector = PrivacyProtector()
        self.intrusion_detector = IntrusionDetector()
        self.security_log = []
    
    async def perform_security_scan(self) -> Dict[str, Any]:
        """انجام اسکن امنیتی جامع"""
        logger.info("Performing comprehensive security scan...")
        
        scan_results = {
            "timestamp": datetime.now().isoformat(),
            "privacy_status": {},
            "intrusion_detection_status": {},
            "overall_status": "CLEAN"
        }
        
        # بررسی حریم خصوصی
        scan_results["privacy_status"] = {
            "browsing_history_paths": self.privacy_protector.browsing_history_paths,
            "temp_directories": self.privacy_protector.temp_dirs
        }
        
        # بررسی نفوذ
        intrusion_check = await self.intrusion_detector.check_for_intrusions()
        scan_results["intrusion_detection_status"] = intrusion_check
        
        if intrusion_check.get("alerts"):
            scan_results["overall_status"] = "WARNING"
        
        self.security_log.append({
            "action": "security_scan",
            "timestamp": datetime.now().isoformat(),
            "results": scan_results
        })
        
        logger.info("Security scan completed.")
        return {"success": True, "results": scan_results}
    
    async def take_action_on_threat(self, alert: Dict[str, Any]) -> Dict[str, Any]:
        """اقدام در برابر تهدید"""
        logger.warning(f"Taking action on threat: {alert.get("description")}")
        
        action_taken = []
        
        if alert.get("type") == "suspicious_process":
            # در یک سیستم واقعی، اینجا باید فرآیند مشکوک را terminate کرد
            action_taken.append("Logged suspicious process. Manual review recommended.")
        elif alert.get("type") == "suspicious_network_connection":
            # در یک سیستم واقعی، اینجا باید اتصال را قطع کرد یا فایروال را تنظیم کرد
            action_taken.append("Logged suspicious network connection. Manual review recommended.")
        elif alert.get("type") == "critical_file_change":
            action_taken.append("Alerted about critical file change. System integrity check recommended.")
            
        self.security_log.append({
            "action": "take_action_on_threat",
            "timestamp": datetime.now().isoformat(),
            "alert": alert,
            "actions": action_taken
        })
        
        return {"success": True, "actions_taken": action_taken}
    
    def get_security_log(self, limit: int = 50) -> List[Dict[str, Any]]:
        """دریافت لاگ امنیتی"""
        return self.security_log[-limit:]


# مثال استفاده (برای تست)
async def main():
    security_manager = SecurityManager()
    
    print("--- Privacy Protection ---")
    await security_manager.privacy_protector.activate_stealth_mode()
    await asyncio.sleep(1)
    await security_manager.privacy_protector.clear_browsing_history()
    await security_manager.privacy_protector.clear_temp_files()
    await security_manager.privacy_protector.deactivate_stealth_mode()
    print(security_manager.privacy_protector.get_privacy_log())
    
    print("\n--- Intrusion Detection ---")
    await security_manager.intrusion_detector.start_monitoring()
    await asyncio.sleep(2) # شبیه‌سازی فعالیت
    scan_result = await security_manager.intrusion_detector.check_for_intrusions()
    print(scan_result)
    if scan_result.get("alerts"):
        for alert in scan_result["alerts"]:
            await security_manager.take_action_on_threat(alert)
            if alert.get("type") == "suspicious_network_connection":
                trace = await security_manager.intrusion_detector.trace_attack_source(alert["description"].split(" ")[5].split(":")[0])
                print(f"Trace result: {trace}")
    await security_manager.intrusion_detector.stop_monitoring()
    print(security_manager.intrusion_detector.get_intrusion_alerts())
    
    print("\n--- Comprehensive Scan ---")
    full_scan = await security_manager.perform_security_scan()
    print(full_scan)
    print(security_manager.get_security_log())

if __name__ == "__main__":
    asyncio.run(main())
