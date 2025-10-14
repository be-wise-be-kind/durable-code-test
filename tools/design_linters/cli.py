#!/usr/bin/env python3
"""
Purpose: Unified CLI for the pluggable design linter framework
Scope: Single extensible interface for all design linting operations
Overview: This module provides a unified command-line interface that consolidates
    all individual linter functionality (SRP analysis, magic number detection,
    print statement linting, etc.) into a single extensible tool that uses
    the pluggable framework architecture.
Dependencies: Framework components, argparse for CLI, pathlib for file operations
Exports: Main CLI interface and configuration management
Interfaces: Provides backward compatibility with existing linter usage
Implementation: Uses framework orchestrator with automatic rule discovery
"""

import argparse
import datetime
import json
import sys
import traceback
from pathlib import Path
from typing import Any

from loguru import logger

from .framework import LintCoordinator, LintViolation, create_orchestrator
from .framework.reporters import ReporterFactory

# Configuration constants for CLI behavior
MAX_METHODS_STRICT = 10
MAX_LINES_STRICT = 200
MAX_METHODS_LENIENT = 25
MAX_LINES_LENIENT = 500
DEFAULT_LINE_SEPARATOR_LENGTH = 40


class ArgumentParser:  # thailint: ignore[srp]  # pylint: disable=too-few-public-methods
    """Handles command-line argument parsing and configuration management."""

    def _create_parser(self) -> argparse.ArgumentParser:
        """Create and configure the argument parser."""
        return argparse.ArgumentParser(
            description="Unified Design Linter - Check code for SOLID principles and style violations",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  # Lint single file
  design-linter myfile.py

  # Lint directory with specific rules
  design-linter src/ --rules solid.srp.too-many-methods,literals.magic-number

  # Output as JSON
  design-linter src/ --format json

  # Show available rules
  design-linter --list-rules

  # Backward compatibility
  design-linter myfile.py --legacy srp  # Same as old srp_analyzer.py
            """,
        )

    def _add_input_arguments(self, parser: argparse.ArgumentParser) -> None:
        """Add input-related arguments."""
        parser.add_argument(
            "paths",
            nargs="*",
            help="Files or directories to lint (default: current directory)",
        )
        parser.add_argument(
            "--recursive",
            "-r",
            action="store_true",
            help="Recursively lint directories",
        )

    def _add_output_arguments(self, parser: argparse.ArgumentParser) -> None:
        """Add output-related arguments."""
        parser.add_argument(
            "--format",
            choices=["text", "json", "sarif", "github"],
            default="text",
            help="Output format",
        )
        parser.add_argument("--output", "-o", help="Output file (default: stdout)")
        parser.add_argument("--no-color", action="store_true", help="Disable colored output")
        parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")

    def _add_rule_arguments(self, parser: argparse.ArgumentParser) -> None:
        """Add rule-related arguments."""
        parser.add_argument("--list-rules", action="store_true", help="List all available rules")
        parser.add_argument("--list-categories", action="store_true", help="List all rule categories")
        parser.add_argument("--rules", help="Comma-separated list of specific rules to run")
        parser.add_argument("--exclude", help="Comma-separated list of rules to exclude")
        parser.add_argument("--categories", help="Comma-separated list of categories to include")
        parser.add_argument(
            "--min-severity",
            choices=["error", "warning", "info"],
            default="info",
            help="Minimum severity level to report",
        )

    def _add_mode_arguments(self, parser: argparse.ArgumentParser) -> None:
        """Add execution mode arguments."""
        parser.add_argument("--strict", action="store_true", help="Use strict checking mode")
        parser.add_argument("--legacy", help="Backward compatibility mode (srp, magic-numbers, etc.)")
        parser.add_argument(
            "--fail-on-error",
            action="store_true",
            help="Exit with non-zero on any errors",
        )
        parser.add_argument("--config", help="Path to configuration file")

    def parse_arguments(self, args: list[str]) -> argparse.Namespace:
        """Parse command-line arguments."""
        parser = self._create_parser()
        self._add_input_arguments(parser)
        self._add_output_arguments(parser)
        self._add_rule_arguments(parser)
        self._add_mode_arguments(parser)
        return parser.parse_args(args)


class ConfigurationLoader:
    """Handles loading configuration from files and defaults."""

    def get_default_config(self) -> dict[str, Any]:
        """Get default configuration."""
        return {"format": "text", "recursive": True, "min_severity": "info"}

    def load_config_file(self, config_path: str) -> dict[str, Any]:
        """Load configuration from file."""
        try:
            with open(config_path, encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, dict) else {}
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error("Failed to load config file %s: %s", config_path, e)
            raise ValueError(f"Failed to load config file {config_path}: {e}") from e

    def apply_config_file(self, config: dict[str, Any], args: argparse.Namespace) -> None:
        """Apply configuration from file if provided."""
        if args.config:
            file_config = self.load_config_file(args.config)
            config.update(file_config)


class ModeConfigApplicator:  # pylint: disable=too-few-public-methods
    """Applies mode-specific configuration overrides."""

    @staticmethod
    def apply_mode_overrides(config: dict[str, Any], args: argparse.Namespace) -> None:
        """Apply mode-specific configuration overrides."""
        if args.strict:
            ModeConfigApplicator.apply_strictness_mode(config)
        if args.legacy:
            ModeConfigApplicator.apply_legacy_mode(config, args.legacy)

    @staticmethod
    def apply_strictness_mode(config: dict[str, Any]) -> None:
        """Apply strict mode configuration."""
        strict_config = ModeConfigApplicator.get_strict_config()
        config.update(strict_config)

    @staticmethod
    def apply_legacy_mode(config: dict[str, Any], legacy_tool: str) -> None:
        """Apply legacy mode configuration."""
        legacy_config = ModeConfigApplicator.get_legacy_config(legacy_tool)
        config.update(legacy_config)

    @staticmethod
    def get_strict_config() -> dict[str, Any]:
        """Get strict mode configuration."""
        return {
            "min_severity": "warning",
            "fail_on_error": True,
            "rules": {
                "solid.srp.too-many-methods": {"max_methods": 10},
                "solid.srp.class-too-big": {"max_lines": MAX_LINES_STRICT},
            },
        }

    @staticmethod
    def get_lenient_config() -> dict[str, Any]:
        """Get lenient mode configuration."""
        return {
            "min_severity": "error",
            "fail_on_error": False,
            "rules": {
                "solid.srp.too-many-methods": {"max_methods": MAX_METHODS_LENIENT},
                "solid.srp.class-too-big": {"max_lines": MAX_LINES_LENIENT},
            },
        }

    @staticmethod
    def get_legacy_config(legacy_tool: str) -> dict[str, Any]:
        """Get configuration for legacy tool compatibility."""
        legacy_configs = {
            "srp": {"categories": ["solid.srp"], "format": "text"},
            "magic": {"categories": ["literals"], "format": "text"},
            "print": {"categories": ["style"], "rules": ["style.print-statement"]},
        }
        return legacy_configs.get(legacy_tool, {})


class RuleFilter:
    """Handles rule filtering and selection."""

    def apply_rule_filters(self, config: dict[str, Any], args: argparse.Namespace) -> None:
        """Apply rule filtering based on arguments."""
        if args.rules:
            self.enable_specific_rules(config, args.rules)
        if args.exclude:
            self.exclude_specific_rules(config, args.exclude)
        if args.categories:
            self.filter_by_categories(config, args.categories)

    def enable_specific_rules(self, config: dict[str, Any], rules_str: str) -> None:
        """Enable only specific rules."""
        self.ensure_rules_dict_exists(config)
        rules_list = [rule.strip() for rule in rules_str.split(",")]

        # First, disable ALL rules by setting a default disabled state
        config["default_rule_enabled"] = False

        # Then enable only the specified rules
        for rule_id in rules_list:
            config["rules"][rule_id] = {"enabled": True}

    def exclude_specific_rules(self, config: dict[str, Any], exclude_str: str) -> None:
        """Exclude specific rules."""
        self.ensure_rules_dict_exists(config)
        exclude_list = [rule.strip() for rule in exclude_str.split(",")]
        for rule_id in exclude_list:
            self.disable_rule(config, rule_id)

    def filter_by_categories(self, config: dict[str, Any], categories_str: str) -> None:
        """Filter rules by categories."""
        categories_list = [cat.strip() for cat in categories_str.split(",")]
        config["categories"] = categories_list

    def ensure_rules_dict_exists(self, config: dict[str, Any]) -> None:
        """Ensure rules dictionary exists in config."""
        if "rules" not in config:
            config["rules"] = {}

    def disable_rule(self, config: dict[str, Any], rule_id: str) -> None:
        """Disable a specific rule."""
        self.ensure_rules_dict_exists(config)
        config["rules"][rule_id] = {"enabled": False}


class ConfigurationFacade:  # pylint: disable=too-few-public-methods
    """Coordinates configuration loading, mode management, and rule filtering."""

    def __init__(self) -> None:
        self.loader = ConfigurationLoader()
        self.mode_manager = ModeConfigApplicator()
        self.rule_filter = RuleFilter()

    def load_configuration(self, args: argparse.Namespace) -> dict[str, Any]:
        """Load and merge configuration from various sources."""
        config = self.loader.get_default_config()
        self.loader.apply_config_file(config, args)
        self.mode_manager.apply_mode_overrides(config, args)
        self.rule_filter.apply_rule_filters(config, args)
        return config

    def _filter_by_categories(self, config: dict[str, Any], categories_str: str) -> None:
        """Filter rules by categories.

        Delegates to RuleFilter.filter_by_categories.
        """
        self.rule_filter.filter_by_categories(config, categories_str)


class RuleListFormatter:  # pylint: disable=too-few-public-methods
    """Formats and displays available rules and categories."""

    def list_rules(self, orchestrator: "LintCoordinator") -> None:
        """List all available rules grouped by category."""
        print("📋 Available Linting Rules")
        print("=" * DEFAULT_LINE_SEPARATOR_LENGTH)
        rules = orchestrator.get_rule_registry().get_all_rules()
        for rule in rules:
            print(f"  • {rule.rule_id}: {rule.rule_name}")

    def list_categories(self, orchestrator: "LintCoordinator") -> None:
        """List all available categories with rule counts."""
        print("📁 Available Rule Categories")
        print("=" * DEFAULT_LINE_SEPARATOR_LENGTH)
        rules = orchestrator.get_rule_registry().get_all_rules()
        categories = set()
        for rule in rules:
            categories.update(rule.categories or ["uncategorized"])
        for category in sorted(categories):
            matching_rules = [r for r in rules if category in (r.categories or ["uncategorized"])]
            count = len(matching_rules)
            print(f"  📂 {category} ({count} rules)")


class OutputFormatter:  # pylint: disable=too-few-public-methods
    """Formats and writes output in various formats."""

    def output_results(
        self,
        violations: list[LintViolation],
        metadata: dict[str, Any],
        args: argparse.Namespace,
    ) -> None:
        """Output linting results in the specified format."""
        reporters = ReporterFactory.get_standard_reporters()
        reporter = reporters[args.format]
        report = reporter.generate_report(violations, metadata)
        self._write_report_output(report, args)

    def _write_report_output(self, report: str, args: argparse.Namespace) -> None:
        """Write report to output destination."""
        if args.output:
            self._write_report_to_file(report, args)
        else:
            logger.info(report)

    def _write_report_to_file(self, report: str, args: argparse.Namespace) -> None:
        """Write report to specified file."""
        try:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(report)
            logger.info("Report written to %s", args.output)
        except OSError as e:
            logger.exception("Error writing to %s: %s", args.output, e)


class LintingExecutor:  # pylint: disable=too-few-public-methods
    """Executes the core linting workflow logic."""

    def __init__(self) -> None:
        self.orchestrator: LintCoordinator | None = None
        self.files_analyzed: int = 0

    def execute_linting(self, args: argparse.Namespace) -> tuple[list[LintViolation], dict[str, Any]]:
        """Execute linting on specified paths.

        Returns violations with metadata.
        """
        config = ConfigurationFacade().load_configuration(args)
        self.orchestrator = self._create_orchestrator(args)

        paths = [Path(p) for p in args.paths] if args.paths else [Path(".")]
        violations = self._lint_all_paths(paths, config, args)
        filtered_violations = self._apply_severity_filter(violations, args)

        metadata = self._generate_metadata(filtered_violations)
        return filtered_violations, metadata

    def _create_orchestrator(self, _args: argparse.Namespace) -> "LintCoordinator":
        """Create and configure the linting orchestrator."""
        try:
            return create_orchestrator()
        except Exception:
            logger.exception("Failed to create orchestrator")
            raise

    def _lint_all_paths(
        self,
        paths: list[Path],
        config: dict[str, Any],
        args: argparse.Namespace,
    ) -> list[LintViolation]:
        """Lint all specified paths."""
        violations = []
        for path in paths:
            if path.exists():
                violations.extend(self._lint_single_path(path, config, args))
        return violations

    def _lint_single_path(self, path: Path, config: dict[str, Any], args: argparse.Namespace) -> list[LintViolation]:
        """Lint a single path (file or directory)."""
        violations = []
        if path.is_file():
            violations.extend(self.orchestrator.lint_file(path, config))
            self.files_analyzed += 1
        elif path.is_dir() and args.recursive:
            for py_file in path.rglob("*.py"):
                violations.extend(self.orchestrator.lint_file(py_file, config))
                self.files_analyzed += 1
        return violations

    def _apply_severity_filter(self, violations: list[LintViolation], args: argparse.Namespace) -> list[LintViolation]:
        """Filter violations by minimum severity level."""
        if not hasattr(args, "min_severity") or not args.min_severity:
            return violations

        from .framework.types import Severity  # pylint: disable=import-outside-toplevel

        min_severity = Severity.from_string(args.min_severity)
        return [v for v in violations if v.severity >= min_severity]

    def _generate_metadata(self, violations: list[LintViolation]) -> dict[str, Any]:
        """Generate metadata about the linting results."""
        return {
            "total_violations": len(violations),
            "files_analyzed": getattr(self, "files_analyzed", 0),
            "timestamp": datetime.datetime.now().isoformat(),
        }


class DesignLinterCLI:  # thailint: ignore[srp]  # pylint: disable=too-few-public-methods
    """Main CLI interface for the unified design linter.

    This class uses composition pattern to delegate responsibilities to
    specialized components, which is why cohesion appears low but the
    design is intentional.
    """

    MSG_LINTING_INTERRUPTED = "❌ Linting interrupted by user"
    EXIT_CODE_INTERRUPTED = 130

    def __init__(self) -> None:
        """Initialize CLI components."""
        self.argument_parser = ArgumentParser()
        self.configuration_manager = ConfigurationFacade()
        self.rule_list_manager = RuleListFormatter()
        self.output_manager = OutputFormatter()
        self.linting_executor = LintingExecutor()

    def run(self, args: list[str] | None = None) -> int:
        """Run the CLI with provided arguments."""
        if args is None:
            args = sys.argv[1:]

        try:
            return self._execute_cli_workflow(args)
        except KeyboardInterrupt:
            logger.error("Linting interrupted by user")
            return self.EXIT_CODE_INTERRUPTED
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.exception("Unhandled exception in CLI execution")
            return self._handle_cli_error(e, locals())

    def _execute_cli_workflow(self, args: list[str]) -> int:
        """Execute the main CLI workflow."""
        parsed_args = self.argument_parser.parse_arguments(args)
        self._setup_logging(parsed_args.verbose)

        orchestrator = self._create_orchestrator(parsed_args)

        # Handle special cases first
        if parsed_args.list_rules:
            self.rule_list_manager.list_rules(orchestrator)
            return 0
        if parsed_args.list_categories:
            self.rule_list_manager.list_categories(orchestrator)
            return 0

        violations, metadata = self.linting_executor.execute_linting(parsed_args)
        self.output_manager.output_results(violations, metadata, parsed_args)

        return self._determine_exit_code(violations, parsed_args)

    def _handle_cli_error(self, error: Exception, local_vars: dict) -> int:
        """Handle CLI execution errors."""
        logger.error("❌ Error during linting: %s", error)

        should_show_traceback = self._should_show_traceback(local_vars)
        if should_show_traceback:
            traceback.print_exc()

        return 1

    def _should_show_traceback(self, local_vars: dict) -> bool:
        """Check if traceback should be shown based on verbose flag."""
        parsed_args = local_vars.get("parsed_args")
        return bool(parsed_args and hasattr(parsed_args, "verbose") and parsed_args.verbose)

    def _setup_logging(self, verbose: bool) -> None:
        """Configure logging based on verbosity level."""
        level = "DEBUG" if verbose else "INFO"
        logger.remove()
        logger.add(sys.stderr, level=level)

    def _create_orchestrator(self, _args: argparse.Namespace) -> "LintCoordinator":
        """Create and configure the linting orchestrator."""
        try:
            return create_orchestrator()
        except Exception:
            logger.exception("Failed to create orchestrator")
            raise

    def _determine_exit_code(self, violations: list[LintViolation], args: argparse.Namespace) -> int:
        """Calculate exit code based on violations and settings."""
        if not violations:
            return 0

        if args.fail_on_error:
            # Return non-zero if violations exist when fail_on_error set
            return 1

        return 0


def main() -> None:
    """Main entry point for the unified design linter CLI."""
    cli = DesignLinterCLI()
    exit_code = cli.run()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
