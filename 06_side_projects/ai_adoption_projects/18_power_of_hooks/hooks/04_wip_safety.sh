#!/usr/bin/env bash
# ============================================================================
# 04_wip_safety.sh — preExit Hook
# ============================================================================
# Purpose:  Auto-stash work-in-progress (WIP) changes when a Claude Code
#           session exits, so no uncommitted work is lost. On next session
#           start, the stash can be popped to restore context.
# Trigger:  Claude Code preExit hook — fires when the session is ending.
# Usage:    Configure in settings.local.json:
#             "hooks": {
#               "preExit": ".claude/hooks/04_wip_safety.sh"
#             }
# Restore:  git stash list
#           git stash pop  (or: git stash apply stash@{0})
# ============================================================================

set -euo pipefail

# ---- Configuration ---------------------------------------------------------
STASH_PREFIX="WIP/CLAUDE_CODE"
LOG_FILE="${HOME}/.claude/hooks/wip_safety.log"
MAX_STASHES=20       # keep at most this many stashes, drop oldest

# ---- Functions -------------------------------------------------------------

log() {
    local level="$1"
    shift
    local timestamp
    timestamp="$(date '+%Y-%m-%d %H:%M:%S')"
    echo "[${timestamp}] [${level}] $*" >> "${LOG_FILE}"
}

is_git_repo() {
    git rev-parse --git-dir &>/dev/null
}

has_uncommitted_changes() {
    # Check for staged, unstaged, or untracked files
    if ! git diff --quiet --cached 2>/dev/null; then
        return 0  # has staged changes
    fi
    if ! git diff --quiet 2>/dev/null; then
        return 0  # has unstaged changes
    fi
    if [[ -n "$(git ls-files --others --exclude-standard 2>/dev/null)" ]]; then
        return 0  # has untracked files
    fi
    return 1  # clean working tree
}

cleanup_old_stashes() {
    local count
    count="$(git stash list | grep -c "${STASH_PREFIX}" 2>/dev/null || true)"
    if [[ "${count}" -gt "${MAX_STASHES}" ]]; then
        local to_drop=$(( count - MAX_STASHES ))
        log "INFO" "Cleaning up ${to_drop} old WIP stash(es)"
        # Drop oldest matching stashes; stash list is LIFO, so oldest are last
        git stash list \
            | grep -n "${STASH_PREFIX}" \
            | sort -rn \
            | tail -n "${to_drop}" \
            | while IFS=: read -r idx _; do
                # stash@{idx} where idx is zero-based index in grep output
                # Convert grep line number to stash index
                local stash_idx=$(( idx - 1 ))
                git stash drop "stash@{${stash_idx}}" 2>/dev/null || true
            done
    fi
}

do_stash() {
    local repo_root
    repo_root="$(git rev-parse --show-toplevel 2>/dev/null)"
    local branch
    branch="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo 'detached')"
    local timestamp
    timestamp="$(date '+%Y-%m-%d %H:%M:%S')"
    local stash_msg="${STASH_PREFIX} ${timestamp} — ${branch}"

    if git stash push --include-untracked --message "${stash_msg}" 2>> "${LOG_FILE}"; then
        log "OK" "Stashed WIP: ${stash_msg} (in ${repo_root})"
        echo ""
        echo "  WIP Safety: Uncommitted changes stashed."
        echo "    Message: ${stash_msg}"
        echo "    Restore: git stash pop"
        echo "    List:    git stash list"
        echo ""
    else
        log "FAIL" "Stash failed in ${repo_root}"
        echo "  WIP Safety: WARNING — failed to stash changes!" >&2
    fi
}

# ---- Main ------------------------------------------------------------------

main() {
    # Create log directory
    mkdir -p "$(dirname "${LOG_FILE}")"

    if ! is_git_repo; then
        log "INFO" "Not a git repository — skipping WIP stash"
        exit 0
    fi

    if ! has_uncommitted_changes; then
        log "INFO" "Working tree clean — no stash needed"
        exit 0
    fi

    log "INFO" "Uncommitted changes detected — stashing"
    do_stash
    cleanup_old_stashes
}

main "$@"
