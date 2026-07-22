import logging
import sys
import os

LOG_FILE = "run_log.txt"

def setup_logger():
    """
    配置全局 Logger：
    同时输出到控制台与 run_log.txt 文件，并确保每条日志立即 flush 刷盘。
    """
    logger = logging.getLogger("VideoNoteTools")
    logger.setLevel(logging.INFO)

    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        "[%(asctime)s.%(msecs)03d] [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S"
    )


    # 1. 控制台 Handler
    try:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    except Exception:
        pass

    # 2. 本地文件 Handler (UTF-8 编码，追加模式)
    try:
        file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        print(f"创建日志文件失败: {e}")

    return logger

_logger = setup_logger()

def log_info(msg):
    """记录 INFO 级别日志并强制刷盘"""
    _logger.info(msg)
    for h in _logger.handlers:
        try:
            h.flush()
        except Exception:
            pass

def log_error(msg):
    """记录 ERROR 级别日志并强制刷盘"""
    _logger.error(msg)
    for h in _logger.handlers:
        try:
            h.flush()
        except Exception:
            pass
