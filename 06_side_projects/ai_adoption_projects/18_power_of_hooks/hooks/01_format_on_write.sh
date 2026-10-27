#!/usr/bin/env bash
# ============================================================================
# 01_format_on_write.sh — afterWrite Hook
# ============================================================================
# Purpose:  Auto-format Python files after they are saved via Claude Code.
#           Runs ruff format (or falls back to black) on .py files.
# Trigger:  Claude Code afterWrite hook — fires after each file write.
# Usage:    Configure in settings.local.json:
#             "hooks": {
#               "afterWrite": ".claude/hooks/01_format_on_write.sh '{file}'"
#             }
# ============================================================================

set -euo pipefail

# ---- Configuration ---------------------------------------------------------
LOG_FILE="${HOME}/.claude/hooks/format_on_write.log"
PYTHON_FORMATTER=""            # auto-detect: ruff > black

# ---- Functions -------------------------------------------------------------

log() {
    local level="$1"
    shift
    local timestamp
    timestamp="$(date '+%Y-%m-%d %H:%M:%S')"
    echo "[${timestamp}] [${level}] $*" >> "${LOG_FILE}"
}

detect_formatter() {
    if command -v ruff &>/dev/null; then
        PYTHON_FORMATTER="ruff format"
    elif command -v black &>/dev/null; then
        PYTHON_FORMATTER="black --quiet"
    else
        log "WARN" "No formatter found (ruff/black). Skipping."
        return 1
    fi
    log "INFO" "Using formatter: ${PYTHON_FORMATTER}"
}

format_file() {
    local file_path="$1"

    # Only process .py files
    if [[ "${file_path}" != *.py ]]; then
        return 0
    fi

    # Skip if file doesn't exist (may have been deleted)
    if [[ ! -f "${file_path}" ]]; then
        log "WARN" "File no longer exists: ${file_path}"
        return 0
    fi

    log "INFO" "Formatting: ${file_path}"

    if ${PYTHON_FORMATTER} "${file_path}" 2>> "${LOG_FILE}"; then
        log "OK"   "Formatted successfully: ${file_path}"
    else
        local exit_code=$?
        log "FAIL" "Formatting failed (exit ${exit_code}): ${file_path}"
        return "${exit_code}"
    fi
}

# ---- Main ------------------------------------------------------------------

main() {
    local file_path="${1:-}"

    if [[ -z "${file_path}" ]]; then
        echo "Usage: 01_format_on_write.sh <file_path>"
        echo "  (This hook is called automatically by Claude Code after writes.)"
        exit 1
    fi

    # Create log directory if missing
    mkdir -p "$(dirname "${LOG_FILE}")"

    if ! detect_formatter; then
        # Logged inside detect_formatter; exit cleanly so the hook chain
        # continues even without a formatter installed.
        exit 0
    fi

    format_file "${file_path}"
}

main "$@"
