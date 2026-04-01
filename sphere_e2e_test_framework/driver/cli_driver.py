import subprocess
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class CLIDriver:
    """
    Flexible CLI execution helper.

    Features
    --------
    - Run CLI with config file
    - Accept list or dict arguments
    - Combine config + extra arguments
    - Capture logs and attach evidence

    Examples
    --------
    cli.run(args=["--help"])

    cli.run(config_file="config.yml")

    cli.run(config_file="config.yml", args=["--verbose"])

    cli.run(
        config_file="config.yml",
        args=["-s", "Utimaco", "-t", "Card", "-m", "Local"]
    )

    cli.run(
        config_file="config.yml",
        args={"-s": "Utimaco", "-t": "Card", "-m": "Local"}
    )
    """

    def __init__(self, executable: str, evidence=None):
        self.executable = executable
        self.evidence = evidence

    # -------------------------------------------------
    # Public API
    # -------------------------------------------------
    def run(self, config_file: str = None, args=None) -> str:
        """
        Execute CLI command.

        Parameters
        ----------
        config_file : str, optional
            Path to config file. Adds '-c <file>'
        args : list or dict, optional
            Additional CLI arguments

            list example:
                ["-s", "Utimaco", "-t", "Card"]

            dict example:
                {"-s": "Utimaco", "-t": "Card"}

        Returns
        -------
        str
            CLI stdout output

        Raises
        ------
        RuntimeError
            If CLI execution fails
        """

        command = [self.executable]

        # Add config
        if config_file:
            command.extend(["-c", config_file])

        # Add arguments (list or dict)
        if args:
            command.extend(self._normalize_args(args))

        formatted_cmd = self._format_command(command)
        logger.info(f"Executing CLI: {formatted_cmd}")

        result = subprocess.run(
            command,
            capture_output=True,
            text=True
        )

        self._save_log(command, result.stdout, result.stderr)

        if result.returncode != 0:
            logger.error("CLI execution failed")
            raise RuntimeError(result.stderr)

        return result.stdout

    # -------------------------------------------------
    # Argument Normalizer
    # -------------------------------------------------
    def _normalize_args(self, args):
        """
        Normalize args into list format.

        Supports:
        - list: ["-s", "Utimaco"]
        - dict: {"-s": "Utimaco"}
        """

        normalized = []

        if isinstance(args, dict):
            for key, value in args.items():
                normalized.append(key)

                # Handle flag-only args
                if value is not None:
                    normalized.append(str(value))

        elif isinstance(args, list):
            normalized.extend(args)

        else:
            raise ValueError("args must be list or dict")

        return normalized

    # -------------------------------------------------
    # Log Saver
    # -------------------------------------------------
    def _save_log(self, command, stdout, stderr) -> Path:
        """
        Save CLI execution output to log file and attach to evidence.
        """

        log_dir = Path("evidence/cli_logs")
        log_dir.mkdir(parents=True, exist_ok=True)

        log_file = log_dir / f"cli_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

        with open(log_file, "w", encoding="utf-8") as f:
            f.write("COMMAND:\n")
            f.write(self._format_command(command) + "\n\n")
            f.write("STDOUT:\n")
            f.write(stdout + "\n\n")
            f.write("STDERR:\n")
            f.write(stderr)

        if self.evidence:
            try:
                self.evidence.attach_file(str(log_file), name="CLI Log")
            except Exception:
                logger.warning("Failed to attach CLI log")

        return log_file

    # -------------------------------------------------
    # Command Formatter (for logging only)
    # -------------------------------------------------
    def _format_command(self, command: list) -> str:
        """
        Format command for logging with quotes.

        Example output:
        "C:/Program Files/TestHsm.Cli.exe" -c "config.yml" -s Utimaco
        """
        formatted = []

        for part in command:
            part = str(part)

            if " " in part or "/" in part or "\\" in part:
                formatted.append(f'"{part}"')
            else:
                formatted.append(part)

        return " ".join(formatted)