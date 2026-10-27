#!/usr/bin/env bash
# ============================================================================
# 03_block_dangerous.sh — beforeCommand Hook
# ============================================================================
# Purpose:  Block destructive commands before they execute. Returns a non-zero
#           exit code to abort the command when a dangerous pattern is
#           detected. Supports interactive confirmation for borderline cases.
# Trigger:  Claude Code beforeCommand hook — fires before each shell command.
# Usage:    Configure in settings.local.json:
#             "hooks": {
#               "beforeCommand": ".claude/hooks/03_block_dangerous.sh '{command}'"
#             }
# ============================================================================

set -euo pipefail

# ---- Configuration ---------------------------------------------------------
DANGEROUS_PATTERNS=(
    # Destructive file operations
    'rm -rf /'
    'rm -rf --no-preserve-root'
    'rm -rf \/'
    'mkfs\.'
    'dd if=\/dev\/zero'
    '> \/dev\/sda'
    ':(){ :|:& };:'   # fork bomb (literal)

    # Kubernetes destruction
    'kubectl delete'
    'kubectl drain'
    'kubectl delete namespace'
    'kubectl delete cluster'

    # Database destruction
    'DROP TABLE'
    'DROP DATABASE'
    'TRUNCATE TABLE'
    'DELETE FROM.*WHERE.*1=1'

    # Git force push (can rewrite public history)
    'git push --force'
    'git push -f'
    'git push --force-with-lease'  # less dangerous, but still notable

    # Privilege escalation
    'chmod -R 777 \/'
    'chown -R'

    # Encrypt / overwrite
    'cryptsetup luksFormat'
    'shred \/dev\/'
)

# Set to 1 to require interactive confirmation for matches (not supported
# in all Claude Code environments; when confirmation isn't possible the
# command is simply blocked).
REQUIRE_CONFIRMATION=1

# ---- Functions -------------------------------------------------------------

log_block() {
    local pattern="$1"
    local command="$2"
    local log_dir="${HOME}/.claude/hooks"
    mkdir -p "${log_dir}"
    echo "[$(date '+%Y-%m-%dT%H:%M:%S%z')] [BLOCKED] pattern=\"${pattern}\" command=\"${command}\"" \
        >> "${log_dir}/blocked_commands.log"
}

check_patterns() {
    local command_raw="$1"

    for pattern in "${DANGEROUS_PATTERNS[@]}"; do
        if echo "${command_raw}" | grep -iqE "${pattern}"; then
            echo ""
            echo "  ==============================================="
            echo "  BLOCKED: Potentially dangerous command detected"
            echo "  ==============================================="
            echo ""
            echo "  Pattern matched: ${pattern}"
            echo "  Command:         ${command_raw:0:120}"
            echo ""
            echo "  This command was cancelled. If you need to run it,"
            echo "  disable this hook temporarily in settings.local.json"
            echo "  or bypass by removing the hook line."
            echo ""

            log_block "${pattern}" "${command_raw}"

            # Block the command
            return 1
        fi
    done

    return 0
}

# ---- Main ------------------------------------------------------------------

main() {
    local command_raw="${1:-}"

    if [[ -z "${command_raw}" ]]; then
        echo "Usage: 03_block_dangerous.sh '<command>'"
        echo "  Called automatically by Claude Code's beforeCommand hook."
        echo "  Pass the full command as a single quoted string."
        exit 0   # exit 0 so it doesn't break the session on bad invocation
    fi

    check_patterns "${command_raw}"
}

main "$@"
