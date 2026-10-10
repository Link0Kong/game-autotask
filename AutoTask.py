# AutoTask.py
import subprocess
import os
import sys
# 检查并安装必需的模块
required_modules = ['psutil']

def install_module(module_name):
    try:
        __import__(module_name)
    except ImportError:
        print(f"正在安装 {module_name}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", module_name])
        print(f"{module_name} 安装完成")

# 检查所有必需的模块
for module in required_modules:
    install_module(module)
import re
import time
import logging
import psutil
import smtplib
import ctypes
import tkinter as tk


from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr
from email.header import Header
from typing import Union, List, Optional

class Config:
    """集中管理所有配置项"""
    SHUTDOWN_ENABLED = True  # 是否启用关机功能
    SHUTDOWN_DELAY = 10       # 关机倒计时（秒）
    MAX_LOG_LENGTH = 5000   # 日志最大长度（字符数）
    
    # 程序路径配置
    ASSISTANT_PROCESS_NAME = "March7th Assistant.exe"
    # 修改为固定路径
    ASSISTANT_PATH = r"G:\autoapps\StarRail\run.bat"  # 修改为批处理脚本路径
    MAA_PATH = r"G:\autoapps\maa\MAA.exe"
    BETTERGI_SCRIPT = r"G:\autoapps\Genshin Impact\run_script.bat"
    BH3_SCRIPT = r"G:\autoapps\bh3\MFW.exe"
    BH3_PROCESS_NAME = "BH3.exe"
    DA_CAPO_PROCESS_NAME = "MFW.exe"
    GENSHIN_EXE = r"G:\miHoYo Launcher\games\Genshin Impact Game\YuanShen.exe"
    
    # 文件路径配置
    LOG_DIR = "今日日志.txt"
    ARCHIVE_LOG = "日志.txt"
    TASK_FLAG_PATH = r"G:\autoapps\task_flag.txt"

    # 超时时间配置
    STARRAIL_DELAY_AFTER_GENSHIN = 10
    WORKFLOW_TIMEOUT = 3600  # 1小时（3600秒）
    PROCESS_START_TIMEOUT = 30  # 进程启动超时时间（秒）
    
    # 流程启用配置
    WORKFLOW_ENABLED = {
        'bh3': True,
        'maa': True,
        'starrail': True,
        'genshin': True
    }
    
    # 系统脚本
    BEGIN_SCRIPT = "begin.bat"
    END_SCRIPT = "end.bat"
    
    # 邮件配置
    SMTP_SERVER = "smtp.qq.com"
    SMTP_PORT = 465
    SENDER_EMAIL = "***REMOVED***"
    RECEIVER_EMAIL = "***REMOVED***"
    EMAIL_PASSWORD = "{{SMTP_AUTH_CODE}}"
    
    # 删除版本匹配模式
    
    # 游戏进程配置
    GAME_PROCESSES = {
        'bh3': {
            'process_names': ['BH3.exe'],
            'start_script': os.path.join(os.path.dirname(__file__), "MFW", "MFW.bat"),
            'timeout': WORKFLOW_TIMEOUT
        },
        'maa': {
            'process_names': ['MAA.exe'],
            'exe_path': os.path.join(os.path.dirname(__file__), "明日方舟", "MAA.exe"),
            'timeout': WORKFLOW_TIMEOUT
        },
        'starrail': {
            'process_names': ['March7th Assistant.exe', 'StarRail.exe'],
            'exe_path': None,
            'timeout': 7200  # 2小时
        },
        'genshin': {
            'process_names': ['BetterGI.exe', 'YuanShen.exe'],
            'start_script': os.path.join(os.path.dirname(__file__), "run_script.bat"),
            'timeout': WORKFLOW_TIMEOUT
        }
    }
    
    @classmethod
    def get_task_flag_path(cls):
        base = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(__file__)
        return os.path.join(base, cls.TASK_FLAG_PATH)
    
    @classmethod
    def get_begin_script(cls):
        base_path = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(__file__)
        return os.path.join(base_path, cls.BEGIN_SCRIPT)
    
    @classmethod
    def get_end_script(cls):
        base_path = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(__file__)
        return os.path.join(base_path, cls.END_SCRIPT)
    
    @classmethod
    def get_log_dir(cls):
        return os.path.join(os.path.dirname(__file__), cls.LOG_DIR)

# ====================== 初始化日志系统 ======================
class Logger:
    """封装日志系统"""
    def __init__(self):
        self._init_logging()
        
    def _init_logging(self):
        """初始化日志系统"""
        os.environ['TZ'] = 'Asia/Shanghai'
        
        log_format = '[%(asctime)s] [%(levelname)s] %(message)s'
        date_format = '%Y-%m-%d %H:%M:%S'
        
        logging.basicConfig(
            level=logging.INFO,
            format=log_format,
            datefmt=date_format,
            handlers=[
                logging.FileHandler(Config.get_log_dir(), encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        open(Config.get_log_dir(), 'w').close()
        self.log_startup_info()
        
    def log_startup_info(self):
        """记录启动信息"""
        logging.info("="*50)
        logging.info("自动化任务系统启动")
        logging.info(f"日志文件: {Config.get_log_dir()}")
        logging.info(f"当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logging.info("="*50)

# ====================== 进程管理 ======================
def is_process_running(process_name: str, timeout: float = 5.0) -> bool:
    """带超时的进程检查函数"""
    start_time = time.time()
    try:
        # 增加初始等待时间，避免立即检查
        time.sleep(2)
        
        for proc in psutil.process_iter(['name']):
            if time.time() - start_time > timeout:
                return False
            if proc.info['name'] == process_name:
                return True
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        pass
    return False

def safe_start_process(
    exe_path: str, 
    timeout: float = Config.PROCESS_START_TIMEOUT,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    creationflags=subprocess.CREATE_NO_WINDOW,
    workdir: Optional[str] = None,
    is_background: bool = False,  # 标记是否为后台任务
    is_launcher: bool = False     # 新增：标记是否为启动器脚本（启动后立即退出）
) -> Optional[subprocess.Popen]:
    """带超时控制的进程启动函数"""
    try:
        logging.info(f"正在启动进程: {exe_path}")
        exe_name = os.path.basename(exe_path)
        
        if exe_path.lower().endswith('.bat'):
            bat_path = os.path.abspath(exe_path)
            command = f'cmd /c "{bat_path}"'
            proc = subprocess.Popen(
                command,
                shell=True,
                stdout=stdout,
                stderr=stderr,
                creationflags=creationflags,
                text=True,
                encoding='utf-8',
                cwd=workdir or os.path.dirname(bat_path))
            
            # 特殊处理启动器脚本（启动后立即退出）
            if is_launcher or is_background:
                logging.info(f"等待启动器脚本完成: {exe_name} (超时: {timeout}秒)")
                try:
                    return_code = proc.wait(timeout=timeout)
                    if return_code == 0:
                        logging.info(f"启动器脚本执行成功: {exe_name}")
                        return proc
                    else:
                        logging.warning(f"启动器脚本执行失败: {exe_name}, 返回码: {return_code}")
                        return None
                except subprocess.TimeoutExpired:
                    logging.warning(f"启动器脚本执行超时: {exe_name}")
                    try:
                        proc.kill()
                        proc.wait(5)
                    except:
                        pass
                    return None
        else:
            proc = subprocess.Popen(
                exe_path,
                stdout=stdout,
                stderr=stderr,
                creationflags=creationflags,
                text=True,
                encoding='utf-8',
                cwd=workdir or os.path.dirname(exe_path))
        
        # 对于需要持续运行的任务
        logging.info(f"等待进程启动... (超时: {timeout}秒)")
        time.sleep(3)  # 初始等待
        
        start_check = time.time()
        while time.time() - start_check < timeout:
            if proc.poll() is not None:
                return_code = proc.returncode
                if return_code == 0:
                    logging.info(f"进程执行完成: {exe_name}, 返回码: {return_code}")
                else:
                    logging.warning(f"进程异常退出: {exe_name}, 返回码: {return_code}")
                return None
                
            if is_process_running(exe_name, 5.0):
                logging.info(f"进程启动成功: {exe_name}")
                return proc
            time.sleep(1)
        
        if proc.poll() is None:
            logging.warning(f"进程启动超时: {exe_name}")
            try:
                proc.kill()
                proc.wait(5)
            except:
                pass
        return None
    except Exception as e:
        logging.error(f"进程启动失败: {str(e)}", exc_info=True)
        return None

def terminate_processes(process_names: Union[str, List[str]], timeout: float = 10.0) -> int:
    """终止指定名称的所有进程（带超时控制）"""
    if isinstance(process_names, str):
        process_names = [process_names]
        
    count = 0
    start_time = time.time()
    for proc in psutil.process_iter(['name', 'pid']):
        if time.time() - start_time > timeout:
            break
        if proc.info['name'] in process_names:
            try:
                proc.kill()
                count += 1
                logging.info(f"已终止进程 {proc.info['name']} PID: {proc.pid}")
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
    return count

def execute_workflow_with_timeout(workflow_func, workflow_name, process_names):
    """带超时控制和重试机制的流程执行函数"""
    start_time = time.time()
    timeout = Config.WORKFLOW_TIMEOUT
    retry_count = 0
    max_retries = 1
    
    while retry_count <= max_retries:
        try:
            logging.info(f"=== 开始{workflow_name}流程 (尝试 {retry_count+1}/{max_retries+1}) ===")
            success = workflow_func()
            elapsed = time.time() - start_time
            if elapsed > timeout:
                logging.error(f"!!! {workflow_name}流程超时 !!!")
                terminate_processes(process_names)
                return False, True
            if success:
                logging.info(f"{workflow_name}流程成功完成")
                return True, False
            logging.warning(f"{workflow_name}流程未成功完成，准备重试")
        except Exception as e:
            logging.error(f"!!! {workflow_name}流程执行异常: {str(e)} !!!", exc_info=True)
        terminate_processes(process_names)
        retry_count += 1
        if retry_count <= max_retries:
            time.sleep(10)  # 增加重试间隔
    
    logging.error(f"!!! {workflow_name}流程失败，已达最大重试次数 !!!")
    return False, False

def execute_bh3_workflow() -> bool:
    """执行崩坏三自动化流程（已删除重试机制）"""
    start_time = time.time()
    timeout = Config.GAME_PROCESSES['bh3']['timeout']
    
    try:
        logging.info("=== 开始崩坏三自动化流程 ===")
        terminate_processes([Config.BH3_PROCESS_NAME, Config.DA_CAPO_PROCESS_NAME])
        time.sleep(3)
        
        process = safe_start_process(
            Config.BH3_SCRIPT,
            timeout=30.0,
            workdir=os.path.dirname(Config.BH3_SCRIPT),
            is_launcher=True  # 标记为启动器脚本
        )
        if not process:
            logging.error("崩坏三脚本启动失败")
            return False
        
        da_capo_started = False
        bh3_started = False
        for _ in range(60):  # 增加检查次数
            if time.time() - start_time > timeout:
                logging.error("崩坏三流程超时")
                return False
            
            if is_process_running(Config.DA_CAPO_PROCESS_NAME, 5.0):
                da_capo_started = True
                logging.info("检测到MFW进程")
                break
            
            if is_process_running(Config.BH3_PROCESS_NAME, 5.0):
                bh3_started = True
                logging.info("检测到BH3进程")
                break
            
            time.sleep(3)
        
        if not da_capo_started and not bh3_started:
            logging.error("未检测到崩坏三相关进程")
            return False
        
        start_monitor_time = time.time()
        monitor_timeout = 3600
        while True:
            if time.time() - start_time > timeout:
                logging.error("崩坏三流程总超时")
                return False
            if time.time() - start_monitor_time > monitor_timeout:
                logging.error("崩坏三监控超时")
                return False
            if not is_process_running(Config.DA_CAPO_PROCESS_NAME, 5.0):
                logging.info("MFW进程已退出")
                break
            time.sleep(5)
        
        time.sleep(10)
        if time.time() - start_time > timeout:
            logging.error("崩坏三流程结束超时")
            return False
        
        if is_process_running(Config.BH3_PROCESS_NAME, 5.0):
            logging.warning("检测到BH3进程仍在运行，尝试终止")
            terminate_processes(Config.BH3_PROCESS_NAME)
            return False
        
        elapsed_min = (time.time() - start_time) / 60
        logging.info(f"崩坏三自动化流程成功完成，耗时: {elapsed_min:.1f}分钟")
        return True
    except Exception as e:
        logging.error(f"崩坏三流程异常: {str(e)}", exc_info=True)
        return False

def execute_maa_workflow() -> bool:
    """执行明日方舟自动化流程"""
    start_time = time.time()
    timeout = Config.GAME_PROCESSES['maa']['timeout']
    
    try:
        logging.info("=== 开始明日方舟自动化流程 ===")
        maa_running = is_process_running("MAA.exe", 10.0)
        if maa_running:
            logging.info("检测到MAA进程正在运行，尝试终止")
            terminate_processes("MAA.exe")
            time.sleep(2)
        
        process = safe_start_process(
            Config.MAA_PATH,
            timeout=15.0,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        if not process:
            logging.error("MAA启动失败")
            return False
        
        try:
            remaining_time = max(1, timeout - (time.time() - start_time))
            logging.info(f"等待MAA完成，剩余时间: {remaining_time:.1f}秒")
            return_code = process.wait(timeout=remaining_time)
            if return_code != 0:
                logging.error(f"MAA返回非零退出码: {return_code}")
                return False
            
            # 检查MAA运行时间，确保不是立即退出的情况
            run_duration = time.time() - start_time
            if run_duration < 30:  # 如果运行时间太短可能是启动失败
                logging.warning(f"MAA运行时间过短 ({run_duration:.1f}秒)，可能未正常执行任务")
                return False
            
            logging.info("明日方舟自动化执行成功")
            return True
        except subprocess.TimeoutExpired:
            logging.error("MAA执行超时")
            process.kill()
            process.wait(5)
            return False
    except Exception as e:
        logging.error(f"MAA流程异常: {str(e)}", exc_info=True)
        return False

def execute_genshin_workflow() -> bool:
    """执行原神自动化流程 - 修复版本"""
    start_time = time.time()
    timeout = Config.GAME_PROCESSES['genshin']['timeout']
    time.sleep(5)  # 初始等待，确保系统稳定
    try:
        logging.info("=== 开始原神自动化流程 ===")
        # 清理现有进程
        for proc in psutil.process_iter(['name', 'exe']):
            if proc.info['name'] == "YuanShen.exe" and proc.info['exe'] == Config.GENSHIN_EXE:
                try:
                    logging.info(f"终止YuanShen进程: PID {proc.pid}")
                    proc.kill()
                    time.sleep(2)
                except:
                    pass
            elif proc.info['name'] == "BetterGI.exe":
                try:
                    logging.info(f"终止BetterGI进程: PID {proc.pid}")
                    proc.kill()
                    time.sleep(2)
                except:
                    pass
        
        # 启动批处理脚本 - 不等待启动器完成
        process = safe_start_process(
            Config.BETTERGI_SCRIPT,
            timeout=30.0,
            workdir=os.path.dirname(Config.BETTERGI_SCRIPT),
            is_launcher=True
        )
        # 即使启动器脚本超时也继续流程
        if not process:
            logging.warning("原神脚本启动超时，但将继续监控进程状态")
        
        # 等待BetterGI进程出现（核心修复点）
        bettergi_started = False
        for _ in range(40):  # 40次*2秒=80秒超时
            if time.time() - start_time > timeout:
                logging.error("原神流程超时")
                return False
            if is_process_running("BetterGI.exe", 5.0):
                bettergi_started = True
                logging.info("检测到BetterGI进程")
                break
            time.sleep(2)
        
        if not bettergi_started:
            logging.error("未检测到BetterGI进程")
            return False
        
        # 等待游戏进程出现
        game_started = False
        for _ in range(80):  # 80次*5秒=400秒超时
            if time.time() - start_time > timeout:
                logging.error("原神游戏启动超时")
                return False
            if is_process_running("YuanShen.exe", 5.0):
                game_started = True
                logging.info("检测到YuanShen进程")
                break
            time.sleep(5)
        
        # 只监控BetterGI和游戏进程状态
        logging.info("监控BetterGI和游戏进程状态...")
        check_interval = 10  # 每10秒检查一次
        max_checks = int(timeout / check_interval)
        
        bettergi_finished = False
        game_finished = False
        
        for _ in range(max_checks):
            current_time = time.time()
            if current_time - start_time > timeout:
                logging.error("原神流程总超时")
                break
                
            # 检查BetterGI状态
            if not bettergi_finished:
                if not is_process_running("BetterGI.exe", 5.0):
                    bettergi_finished = True
                    logging.info("BetterGI进程已退出")
            
            # 检查游戏状态
            if not game_finished:
                if not is_process_running("YuanShen.exe", 5.0):
                    game_finished = True
                    logging.info("YuanShen进程已退出")
            
            # 两个进程都退出则结束监控
            if bettergi_finished and game_finished:
                logging.info("BetterGI和游戏进程均已退出")
                break
                
            time.sleep(check_interval)
        else:
            logging.warning("等待进程退出超时")
        
        # 清理残留进程
        if not bettergi_finished:
            logging.warning("BetterGI进程仍在运行，尝试终止")
            terminate_processes("BetterGI.exe")
        if not game_finished:
            logging.warning("YuanShen进程仍在运行，尝试终止")
            terminate_processes("YuanShen.exe")
        
        end_time = time.time()
        duration = end_time - start_time
        logging.info(f"原神自动化流程完成，耗时: {duration/60:.1f}分钟")
        
        # 成功条件：BetterGI和游戏进程都已完成
        return bettergi_finished and game_finished
    except Exception as e:
        logging.error(f"原神流程异常: {str(e)}", exc_info=True)
        return False

def execute_starrail_workflow() -> bool:
    """执行星穹铁道自动化流程"""
    start_time = time.time()
    timeout = Config.GAME_PROCESSES['starrail']['timeout']
    task_flag_path = Config.TASK_FLAG_PATH  # 直接使用固定路径
    
    try:
        logging.info("=== 开始星穹铁道自动化流程 ===")
        logging.info(f"任务标志文件路径: {task_flag_path}")  # 记录实际使用的路径
        
        # 确保任务标志文件不存在（清理上次的残留）
        if os.path.exists(task_flag_path):
            try:
                os.remove(task_flag_path)
                logging.info("已清理旧的任务标志文件")
            except Exception as e:
                logging.error(f"删除旧标志文件失败: {str(e)}")
        
        # 终止正在运行的小助手进程
        if is_process_running(Config.ASSISTANT_PROCESS_NAME, 5.0):
            logging.info("检测到小助手进程正在运行，尝试终止")
            terminate_processes(Config.ASSISTANT_PROCESS_NAME)
            time.sleep(2)
        
        # 使用固定路径启动脚本
        assistant_path = Config.ASSISTANT_PATH
        if not os.path.exists(assistant_path):
            logging.error(f"星穹铁道启动脚本路径不存在: {assistant_path}")
            return False
            
        # 使用批处理脚本启动
        process = safe_start_process(
            assistant_path,
            timeout=15.0,
            workdir=os.path.dirname(assistant_path),
            is_launcher=True
        )
        if not process:
            logging.error("星穹铁道启动脚本执行失败")
            return False
        
        # 增加等待时间确保进程启动
        assistant_started = False
        for _ in range(60):  # 增加检查次数和超时时间
            if time.time() - start_time > timeout:
                logging.error("星穹铁道流程超时")
                return False
            if is_process_running(Config.ASSISTANT_PROCESS_NAME, 5.0):
                assistant_started = True
                logging.info("检测到小助手进程")
                break
            time.sleep(3)
        
        if not assistant_started:
            logging.error("未检测到小助手进程")
            return False
        
        # 监控小助手进程并等待任务完成标志
        task_completed = False
        start_monitor_time = time.time()
        monitor_timeout = 7200  # 2小时超时
        process_exited = False  # 跟踪进程退出状态
        
        while not task_completed:
            current_time = time.time()
            # 检查总超时
            if current_time - start_time > timeout:
                logging.error("星穹铁道流程总超时")
                return False
                
            # 检查监控超时
            if current_time - start_monitor_time > monitor_timeout:
                logging.error("星穹铁道监控超时")
                return False
                
            # 检查进程是否仍在运行（只记录一次退出）
            if not process_exited:
                if not is_process_running(Config.ASSISTANT_PROCESS_NAME, 5.0):
                    logging.info("小助手进程已退出")
                    process_exited = True
                    # 进程退出后增加额外等待时间确保文件被创建
                    time.sleep(10)
            
            # 检查任务标志文件 - 简化检测逻辑：文件存在即视为任务完成
            if os.path.exists(task_flag_path):
                task_completed = True
                logging.info("检测到任务标志文件")
                # 删除文件以便下次使用
                try:
                    os.remove(task_flag_path)
                except Exception as e:
                    logging.error(f"删除任务标志文件失败: {str(e)}")
                break
            elif process_exited:
                # 进程已退出但文件不存在
                logging.warning("小助手进程已退出，但未检测到任务标志文件")
                break
            
            # 等待一段时间再次检查
            time.sleep(10)
        
        # 确保清理进程
        terminate_processes(Config.ASSISTANT_PROCESS_NAME)
        return task_completed
    except Exception as e:
        logging.error(f"星穹铁道流程异常: {str(e)}", exc_info=True)
        return False

def terminate_all_assistants() -> int:
    """终止所有小助手进程"""
    return terminate_processes(Config.ASSISTANT_PROCESS_NAME)

# ====================== 关机倒计时窗口 ======================
class ShutdownGUI:
    def __init__(self, total_seconds):
        self.root = tk.Tk()
        self.root.title("关机倒计时")
        self.root.attributes('-topmost', True)
        self.cancelled = False
        self.remaining = total_seconds
        self.label = tk.Label(self.root, font=('Arial', 24))
        self.label.pack(padx=20, pady=10)
        self.cancel_btn = tk.Button(
            self.root,
            text="取消关机",
            font=('Arial', 14),
            command=self.cancel_shutdown
        )
        self.cancel_btn.pack(pady=10)
        self.update_display()
        self.root.after(1000, self.countdown)

    def update_display(self):
        self.label.config(text=f"将在 {self.remaining} 秒后关机")

    def cancel_shutdown(self):
        self.cancelled = True
        self.root.destroy()
        logging.info("用户已取消关机操作")

    def countdown(self):
        if self.cancelled:
            return
        self.remaining -= 1
        if self.remaining > 0:
            self.update_display()
            self.root.after(1000, self.countdown)
        else:
            self.root.destroy()
            if not self.cancelled:
                os.system("shutdown /s /t 1")

# 删除 find_latest_assistant 函数

# ====================== 邮件服务 ======================
def construct_email(error_details=None):
    """构造任务完成通知邮件"""
    error_occurred = False
    error_summary = "正常"
    
    if error_details:
        error_status = []
        for game, details in error_details.items():
            if details['timeout'] or details['failed']:
                error_status.append(f"{game}失败")
                error_occurred = True
        
        if error_status:
            error_summary = "异常:" + ",".join(error_status)
    
    status = "【异常】" if error_occurred else "【正常】"
    subject = f"{status}每日任务完成报告[{error_summary}]"
    
    msg = MIMEMultipart()
    msg['From'] = formataddr(("自动任务系统", Config.SENDER_EMAIL))
    msg['To'] = Config.RECEIVER_EMAIL
    msg['Subject'] = Header(subject, 'utf-8')
    msg['Date'] = datetime.now().strftime('%a, %d %b %Y %H:%M:%S %z')

    body = f"""任务状态报告
    完成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    任务摘要：{error_summary}
    
    ==== 今日日志内容 ====
    """
    
    try:
        log_dir = Config.get_log_dir()
        with open(log_dir, 'r', encoding='utf-8') as f:
            log_content = f.read(Config.MAX_LOG_LENGTH)
            if len(log_content) == Config.MAX_LOG_LENGTH:
                log_content += "\n...(日志内容已截断)"
    except Exception as e:
        log_content = f"\n无法读取日志文件: {str(e)}\n"

    body += f"\n{log_content}\n"
    msg.attach(MIMEText(body, 'plain', 'utf-8'))
    return msg

def safe_send_email(error_details=None):
    server = None
    try:
        logging.info("尝试发送邮件...")
        server = smtplib.SMTP_SSL(Config.SMTP_SERVER, Config.SMTP_PORT, timeout=10)
        server.login(Config.SENDER_EMAIL, Config.EMAIL_PASSWORD)
        server.sendmail(Config.SENDER_EMAIL, [Config.RECEIVER_EMAIL], construct_email(error_details).as_string())
        logging.info("邮件发送成功")
        return True
    except Exception as e:
        logging.error(f"邮件发送失败: {str(e)}")
        return False
    finally:
        if server:
            try:
                server.quit()
            except Exception:
                pass

def safe_execute_process(process_name, process_path, max_retries=1, timeout=60):
    """安全执行系统脚本（如begin.bat/end.bat）"""
    retry_count = 0
    while retry_count < max_retries:
        logging.info(f"执行系统脚本: {process_name} (尝试 {retry_count+1}/{max_retries})")
        
        # 使用新的is_background参数标记后台任务
        process = safe_start_process(
            process_path,
            timeout=timeout,
            workdir=os.path.dirname(process_path),
            is_background=True  # 标记为后台任务
        )
        
        if process:
            logging.info(f"{process_name}执行成功")
            return True
        else:
            logging.warning(f"{process_name}执行失败")
        
        retry_count += 1
        if retry_count < max_retries:
            time.sleep(5)
    
    logging.error(f"{process_name}执行失败，已达最大重试次数")
    return False

# ====================== 时间检查函数 ======================
def after_4am() -> bool:
    """检查当前时间是否在凌晨4点之后"""
    now = datetime.now()
    return now.hour >= 4

def wait_until_4am():
    """等待直到凌晨4点"""
    now = datetime.now()
    if now.hour < 4:
        target_time = now.replace(hour=4, minute=0, second=0, microsecond=0)
    else:
        tomorrow = now + timedelta(days=1)
        target_time = tomorrow.replace(hour=4, minute=0, second=0, microsecond=0)
    
    wait_seconds = (target_time - now).total_seconds()
    logging.info(f"等待到凌晨4点 ({wait_seconds/3600:.1f}小时)...")
    
    while wait_seconds > 0:
        sleep_time = min(600, wait_seconds)
        time.sleep(sleep_time)
        wait_seconds -= sleep_time
    logging.info("时间已到凌晨4点，继续执行任务")

# ====================== 主工作流程 ======================
def main_workflow():
    """自动化任务主工作流程"""
    error_details = {
        'bh3': {'failed': False, 'timeout': False},
        'maa': {'failed': False, 'timeout': False},
        'genshin': {'failed': False, 'timeout': False},
        'starrail': {'failed': False, 'timeout': False}
    }
    error_flag = False
    genshin_end_time = None
    task_completed = False  # 确保变量被定义
    
    try:
        Logger()
        logging.info("===== 自动化任务流程开始 =====")
        
        # 只执行一次系统预处理
        if not safe_execute_process("系统预处理", Config.get_begin_script(), timeout=60):
            error_flag = True
            logging.error("系统预处理失败")
        else:
            logging.info("系统预处理完成")
        
        if Config.WORKFLOW_ENABLED['bh3']:
            # 直接执行崩坏三流程，不进行重试
            logging.info("=== 开始崩坏三流程 (无重试机制) ===")
            start_time = time.time()
            success = execute_bh3_workflow()
            elapsed = time.time() - start_time
            timeout = Config.GAME_PROCESSES['bh3']['timeout']
            
            if elapsed > timeout:
                logging.error("!!! 崩坏三流程超时 !!!")
                error_details['bh3']['timeout'] = True
                terminate_processes(Config.GAME_PROCESSES['bh3']['process_names'])
            else:
                error_details['bh3']['failed'] = not success
            
            if success:
                logging.info("崩坏三流程成功完成")
            else:
                logging.error("崩坏三流程失败")
        
        other_enabled = any(Config.WORKFLOW_ENABLED[wf] for wf in ['maa', 'genshin', 'starrail'])
        if other_enabled and not after_4am():
            wait_until_4am()
        
        if Config.WORKFLOW_ENABLED['maa']:
            maa_config = Config.GAME_PROCESSES['maa']
            success, timed_out = execute_workflow_with_timeout(
                execute_maa_workflow,
                "明日方舟",
                maa_config['process_names']
            )
            error_details['maa']['failed'] = not success
            error_details['maa']['timeout'] = timed_out
            if not success:
                error_flag = True
        
        if Config.WORKFLOW_ENABLED['genshin']:
            genshin_config = Config.GAME_PROCESSES['genshin']
            genshin_start_time = time.time()
            success, timed_out = execute_workflow_with_timeout(
                execute_genshin_workflow,
                "原神",
                genshin_config['process_names']
            )
            genshin_end_time = time.time()
            error_details['genshin']['failed'] = not success
            error_details['genshin']['timeout'] = timed_out
            if not success:
                error_flag = True
        
        if Config.WORKFLOW_ENABLED['starrail']:
            delay_remaining = 0
            if Config.WORKFLOW_ENABLED['genshin'] and genshin_end_time is not None:
                elapsed_since_genshin = time.time() - genshin_end_time
                delay_remaining = max(0, Config.STARRAIL_DELAY_AFTER_GENSHIN - elapsed_since_genshin)
            elif other_enabled:
                delay_remaining = Config.STARRAIL_DELAY_AFTER_GENSHIN
            
            if delay_remaining > 0:
                logging.info(f"等待星穹铁道启动延迟: 10秒")
                time.sleep(delay_remaining)
            
            starrail_config = Config.GAME_PROCESSES['starrail']
            success, timed_out = execute_workflow_with_timeout(
                execute_starrail_workflow,
                "星穹铁道",
                starrail_config['process_names']
            )
            error_details['starrail']['failed'] = not success
            error_details['starrail']['timeout'] = timed_out
            task_completed = success
        
        # 无论任务是否完成都发送邮件报告
        safe_send_email(error_details)
        
        # 执行系统恢复脚本
        end_script = Config.get_end_script()
        if os.path.exists(end_script):
            safe_execute_process("系统恢复", end_script)
        
        # 关机处理 - 修改为只要启用了关机功能就尝试关机
        if Config.SHUTDOWN_ENABLED:
            logging.info("准备关机，显示倒计时窗口...")
            shutdown_gui = ShutdownGUI(Config.SHUTDOWN_DELAY)
            shutdown_gui.root.mainloop()
            if not shutdown_gui.cancelled:
                logging.info("用户未取消关机，即将关机...")
                time.sleep(2)
                os.system("shutdown /s /t 1")
            else:
                logging.info("用户取消了关机操作")
        else:
            logging.info("关机功能未启用，跳过关机")
    
    except Exception as e:
        logging.error(f"主工作流程异常: {str(e)}", exc_info=True)
    finally:
        logging.info("清理残留进程...")
        terminate_all_assistants()
        for proc_name in [Config.BH3_PROCESS_NAME, "BetterGI.exe", "MAA.exe"]:
            terminate_processes(proc_name)
        
        try:
            # 归档日志
            with open(Config.get_log_dir(), 'r', encoding='utf-8') as src, \
                 open(Config.ARCHIVE_LOG, 'a', encoding='utf-8') as dest:
                dest.write(f"\n{'='*50}\n")
                dest.write(f"任务结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                dest.write(src.read())
            logging.info("日志归档完成")
        except Exception as e:
            logging.error(f"日志归档失败: {str(e)}")
        
        logging.info("===== 自动化任务流程结束 =====")

if __name__ == "__main__":
    if ctypes.windll.shell32.IsUserAnAdmin() == 0:
        logging.info("请求管理员权限...")
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, f'"{__file__}"', None, 1)
        sys.exit()
    main_workflow()