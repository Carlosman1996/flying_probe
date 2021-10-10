import logging


logging.basicConfig(level=logging.INFO, format='%(asctime)s : %(levelname)s : %(name)s : %(message)s')


__author__ = "Carlos Manuel Molina Sotoca"
__email__ = "cmmolinas01@gmail.com"


class Logger:
    def __init__(self, module=__name__, level="INFO", logs_file=False):
        self.logger = logging.getLogger(module)
        self.set_logger_level(level)
        self.set_logs_file(logs_file, module)

    def set_logger_level(self, level):
        if level == "DEBUG":
            self.logger.setLevel(logging.DEBUG)
        elif level == "INFO":
            self.logger.setLevel(logging.INFO)
        elif level == "WARNING":
            self.logger.setLevel(logging.WARNING)
        elif level == "ERROR":
            self.logger.setLevel(logging.ERROR)
        elif level == "CRITICAL":
            self.logger.setLevel(logging.CRITICAL)
        else:
            raise Exception("Logging level does not exist. Supported levels: DEBUG, INFO, WARNING, ERROR and CRITICAL")

    def set_logs_file(self, logs_file, module):
        if logs_file:
            # Define file handler and set formatter:
            file_handler = logging.FileHandler(f'{module}_logfile.log')
            formatter = logging.Formatter('%(asctime)s : %(levelname)s : %(name)s : %(message)s')
            file_handler.setFormatter(formatter)

            # Add file handler to logger:
            self.logger.addHandler(file_handler)

    def set_message(self, level, message_level, message):
        # Modify message depending on level:
        if message_level == "SECTION":
            message = f" ########## {message.upper()} ##########"
        elif message_level == "SUBSECTION":
            message = f" ---------- {message} ----------"
        else:
            message = f"\t\t {message}"

        # Write message:
        if level == "DEBUG":
            self.logger.debug(message)
        elif level == "INFO":
            self.logger.info(message)
        elif level == "WARNING":
            self.logger.warning(message)
        elif level == "ERROR":
            self.logger.error(message)
        elif level == "CRITICAL":
            self.logger.critical(message)
        else:
            raise Exception("Logging level does not exist. Supported levels: DEBUG, INFO, WARNING, ERROR and CRITICAL")
