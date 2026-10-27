#!/usr/bin/env bash
# ============================================================================
# 02_audit_trail.sh — afterCommand Hook
# ============================================================================
# Purpose:  Log every shell command Claude Code executes to an audit trail.
#           Captures timestamp, command text, exit code, and working directory.
# Trigger:  Claude Code afterCommand hook — fires after each shell command.
# Usage:    Configure in settings.local.json:
#             "hooks": {
#               "afterCommand": ".claude/hooks/02_audit_trail.sh '{command}' {exit_code}"
#             }
# Query:    grep some_command ~/.claude/hooks/audit_trail.log
#           tail -f ~/.claude/hooks/audit_trail.log
# ============================================================================

set -euo pipefail

# ---- Configuration ---------------------------------------------------------
AUDIT_DIR="${HOME}/.claude/hooks"
AUDIT_FILE="${AUDIT_DIR}/audit_trail.log"
MAX_LOG_SIZE_MB=50   # rotate when log exceeds this

# ---- Functions -------------------------------------------------------------

init_audit_dir() {
    mkdir -p "${AUDIT_DIR}"
}

rotate_if_needed() {
    if [[ -f "${AUDIT_FILE}" ]]; then
        local size_kb
        size_kb="$(du -k "${AUDIT_FILE}" | cut -f1)"
        local max_kb=$(( MAX_LOG_SIZE_MB * 1024 ))
        if (( size_kb > max_kb )); then
            local rotated="${AUDIT_FILE}.$(date '+%Y%m%d-%H%M%S')"
            mv "${AUDIT_FILE}" "${rotated}"
            gzip "${rotated}" 2>/dev/null || true
        fi
    fi
}

log_entry() {
    local command_raw="$1"
    local exit_code="$2"

    # The {command} variable is passed JSON-escaped; we store it as-is.
    # Strip surrounding quotes if present.
    command_raw="${command_raw#\"}"
    command_raw="${command_raw%\"}"

    local timestamp
    timestamp="$(date '+%Y-%m-%dT%H:%M:%S%z')"
    local cwd
    cwd="$(pwd)"
    local session_id="${CLAUDE_CODE_SESSION_ID:-unknown}"

    # Tab-separated for easy grep/awk processing:
    #   timestamp  |  session_id  |  exit_code  |  working_dir  |  command
    printf "%s\t%s\t%s\t%s\t%s\n" \
        "${timestamp}" \
        "${session_id}" \
        "${exit_code}" \
        "${cwd}" \
        "${command_raw}" \
        >> "${AUDIT_FILE}"
}

# ---- Usage / Help ---------------------------------------------------------

show_query_examples() {
    cat <<'HELP'

  Query the audit trail:
  ----------------------
  # Recent commands
  tail -20 ~/.claude/hooks/audit_trail.log

  # Commands with exit code != 0 (failures)
  awk '$3 != 0' ~/.claude/hooks/audit_trail.log

  # Commands containing a keyword
  grep 'git push' ~/.claude/hooks/audit_trail.log

  # Sessions summary
  cut -f2 ~/.claude/hooks/audit_trail.log | sort | uniq -c | sort -rn

  # Last session commands
  sid=$(tail -1 ~/.claude/hooks/audit_trail.log | cut -f2)
  awk -v s="$sid" '$2 == s' ~/.claude/hooks/audit_trail.log

HELP
}

# ---- Main ------------------------------------------------------------------

main() {
    local command_raw="${1:-}"
    local exit_code="${2:-}"

    if [[ -z "${command_raw}" ]]; then
        echo "Usage: 02_audit_trail.sh '<command>' <exit_code>"
        echo ""
        echo "  Called automatically by Claude Code's afterCommand hook."
        echo "  The command should be passed as a single quoted string."
        echo ""
        show_query_examples
        exit 1
    fi

    init_audit_dir
    rotate_if_needed
    log_entry "${command_raw}" "${exit_code}"
}

main "$@"
