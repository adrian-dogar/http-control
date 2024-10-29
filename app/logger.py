import logging
import sys

class ColoredFormatter(logging.Formatter):
    COLORS = {
        'DEBUG': '\033[94m',    # Blue
        'INFO': '\033[0m',      # White
        'INFO_GREEN': '\033[92m', # Green
        'WARNING': '\033[93m',  # Yellow
        'ERROR': '\033[91m',    # Red
        'CRITICAL': '\033[95m', # Magenta
        'RESET': '\033[0m'      # Reset color
    }

    def format(self, record):
        if record.levelname == 'INFO' and record.msg.startswith('Assertion passed'):
            color = self.COLORS['INFO_GREEN']
        else:
            color = self.COLORS.get(record.levelname, self.COLORS['RESET'])

        log_message = super().format(record)
        return f"{color}{log_message}{self.COLORS['RESET']}"

def setup_logger(name='project_logger', level=logging.DEBUG):
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Check if the logger already has handlers
    if not logger.handlers:
        # Create stdout handler
        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler.setLevel(level)

        # Create formatter
        formatter = ColoredFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        stdout_handler.setFormatter(formatter)

        # Add handler to logger
        logger.addHandler(stdout_handler)

    return logger