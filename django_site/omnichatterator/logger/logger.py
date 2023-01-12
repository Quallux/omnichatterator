import os
import shutil
import json
from datetime import datetime

from .logger_sink import LoggerSink

# LOGGER SETUP - runs on server startup
logger_root = "omnichatterator/logger"
logs_directory = logger_root + "/logs"
if os.path.exists(logs_directory):
    shutil.rmtree(logs_directory)
os.mkdir(logs_directory)

logger_settings_path = logger_root + "/logger_settings.json"
log_file_path = logs_directory + "/log.txt"

try:
    with open(logger_settings_path, "r") as json_settings_file:
        json_settings_data = json.loads(json_settings_file.read())
        console_sinks = json_settings_data["CONSOLE_SINKS"]
        log_file_sinks = json_settings_data["LOG_FILE_SINKS"]
        separately_logged_sinks = json_settings_data["SEPARATELY_LOGGED_SINKS"]
except:
    console_sinks = "ALL"
    log_file_sinks = "ALL"
    separately_logged_sinks = "ALL"


def log(message: str, logger_sink: LoggerSink = LoggerSink.DEFAULT):
    """
    used for logging

    :param message: message to be logged
    :param logger_sink: sink for logged message
    :return: does not return any value
    """

    log_message = str(datetime.now()) + " [" + str(logger_sink.value) + "] - " + message

    # SEPARATELY LOGGED SINKS
    if logger_sink.value in separately_logged_sinks or separately_logged_sinks == "ALL":
        sink_log_file_path = logs_directory + "/" + logger_sink.value + ".txt"
        with open(sink_log_file_path, "a", encoding="utf-8") as sink_log_file:
            sink_log_file.write(log_message + "\n")

    # LOG FILE LOGGING (log.txt)
    if logger_sink.value in log_file_sinks or log_file_sinks == "ALL":
        with open(log_file_path, "a", encoding="utf-8") as log_file:
            log_file.write(log_message + "\n")

    # CONSOLE LOGGING
    if logger_sink.value in console_sinks or console_sinks == "ALL":
        print(log_message)
