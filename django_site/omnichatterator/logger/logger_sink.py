from enum import Enum


class LoggerSink(Enum):
    # you can create your own sinks, but keep the attribute name equal to its value (both uppercase)
    DEFAULT = "DEFAULT"
    TWITTER = "TWITTER"
    VIEW = "VIEW"
    MESSENGER = "MESSENGER"
    MESSENGER_LOGIN = "MESSENGER_LOGIN"
    GMAIL = "GMAIL"
    PLATFORM_ERRS = "PLATFORM_ERRS"
    GMAIL_TESTING = "GMAIL_TESTING"

