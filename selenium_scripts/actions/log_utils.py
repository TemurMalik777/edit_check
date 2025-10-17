import logging

logging.basicConfig(
    filename="logs/automation.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def log(log_panel, msg, level="info"):
    try:
        if callable(log_panel):
            log_panel(msg)
        else:
            log_panel.append(msg)
    except Exception:
        print(msg)

    getattr(logging, level, logging.info)(msg)
