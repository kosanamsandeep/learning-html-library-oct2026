#!/usr/bin/env bash
# ============================================================================
# test_hooks.sh — Hook Test Suite
# ============================================================================
# Purpose:  Validate each hook script works correctly in isolation.
#           Runs in a temporary directory to avoid side effects.
# Usage:    bash test_hooks.sh
# Returns:  0 if all tests pass, 1 otherwise.
# ============================================================================

set -euo pipefail

TEST_DIR=""
PASS_COUNT=0
FAIL_COUNT=0
HOOKS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/hooks"

# ---- Colors ---------------------------------------------------------------
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# ---- Setup / Teardown -----------------------------------------------------

setup() {
    TEST_DIR="$(mktemp -d /tmp/hook_test_XXXXXX)"
    # Symlink hooks into test dir so scripts can reference paths
    ln -sf "${HOOKS_DIR}" "${TEST_DIR}/hooks"
    cd "${TEST_DIR}"
    echo "  Test directory: ${TEST_DIR}"
}

teardown() {
    if [[ -n "${TEST_DIR}" && -d "${TEST_DIR}" ]]; then
        rm -rf "${TEST_DIR}"
    fi
}

pass() {
    local msg="$1"
    PASS_COUNT=$(( PASS_COUNT + 1 ))
    echo -e "  ${GREEN}[PASS]${NC} ${msg}"
}

fail() {
    local msg="$1"
    FAIL_COUNT=$(( FAIL_COUNT + 1 ))
    echo -e "  ${RED}[FAIL]${NC} ${msg}"
}

# ---- Test: 01_format_on_write.sh ------------------------------------------

test_format_on_write() {
    echo ""
    echo "--- Test: 01_format_on_write.sh ---"

    # Create a deliberately unformatted Python file
    cat > "${TEST_DIR}/bad_format.py" <<'PYEOF'
def hello(  ):
    x=1+2
    return   x

PYEOF

    # Run the hook
    bash "${HOOKS_DIR}/01_format_on_write.sh" "${TEST_DIR}/bad_format.py" 2>&1 || true

    # Check if the file was formatted (ruff/black should have cleaned it)
    if grep -q "def hello():" "${TEST_DIR}/bad_format.py" 2>/dev/null || grep -q "x = 1 + 2" "${TEST_DIR}/bad_format.py" 2>/dev/null; then
        pass "Formatting applied to bad_format.py"
    else
        # Might not have ruff/black installed — check log for evidence
        if grep -q "No formatter found" "${HOME}/.claude/hooks/format_on_write.log" 2>/dev/null; then
            pass "Formatter not installed (skipped gracefully)"
        else
            fail "Formatting did not run or produced unexpected output"
            echo "       File content:"
            cat "${TEST_DIR}/bad_format.py" | sed 's/^/       /'
        fi
    fi

    # Test non-Python file is skipped
    echo "not python" > "${TEST_DIR}/not_python.txt"
    local before_mtime
    before_mtime="$(stat -c %Y "${TEST_DIR}/not_python.txt")"
    bash "${HOOKS_DIR}/01_format_on_write.sh" "${TEST_DIR}/not_python.txt"
    local after_mtime
    after_mtime="$(stat -c %Y "${TEST_DIR}/not_python.txt")"
    if [[ "${before_mtime}" == "${after_mtime}" ]]; then
        pass "Non-Python file correctly skipped"
    else
        fail "Non-Python file was modified"
    fi

    # Test missing file handled gracefully
    local output
    output="$(bash "${HOOKS_DIR}/01_format_on_write.sh" "${TEST_DIR}/nonexistent.py" 2>&1 || true)"
    if [[ -z "$(echo "${output}" | grep -i 'error')" ]]; then
        pass "Missing file handled without error"
    else
        fail "Missing file produced an error: ${output}"
    fi
}

# ---- Test: 02_audit_trail.sh ----------------------------------------------

test_audit_trail() {
    echo ""
    echo "--- Test: 02_audit_trail.sh ---"

    local audit_file="${HOME}/.claude/hooks/audit_trail.log"
    rm -f "${audit_file}"

    # Log a test command
    bash "${HOOKS_DIR}/02_audit_trail.sh" "echo hello world" "0"

    if [[ -f "${audit_file}" ]]; then
        local line
        line="$(tail -1 "${audit_file}")"
        if echo "${line}" | grep -q "echo hello world"; then
            pass "Command logged correctly in audit trail"
        else
            fail "Audit log entry missing expected command"
            echo "       Got: ${line}"
        fi
        if echo "${line}" | grep -q "0"; then
            pass "Exit code 0 logged correctly"
        else
            fail "Exit code missing in log entry"
        fi
    else
        fail "Audit log file not created at ${audit_file}"
    fi

    # Test with non-zero exit code
    bash "${HOOKS_DIR}/02_audit_trail.sh" "failing_command" "1"
    local line2
    line2="$(tail -1 "${audit_file}")"
    if echo "${line2}" | grep -q "1"; then
        pass "Non-zero exit code logged correctly"
    else
        fail "Non-zero exit code not captured"
    fi
}

# ---- Test: 03_block_dangerous.sh ------------------------------------------

test_block_dangerous() {
    echo ""
    echo "--- Test: 03_block_dangerous.sh ---"

    # Test patterns that should be blocked
    local dangerous_commands=(
        "rm -rf /"
        "rm -rf --no-preserve-root /var"
        "kubectl delete pod nginx"
        "DROP TABLE users;"
        "git push --force origin main"
        "git push -f origin main"
    )

    for cmd in "${dangerous_commands[@]}"; do
        if bash "${HOOKS_DIR}/03_block_dangerous.sh" "${cmd}" 2>&1; then
            fail "Command should have been blocked: ${cmd}"
        else
            pass "Correctly blocked: ${cmd:0:50}"
        fi
    done

    # Test safe commands that should be allowed
    local safe_commands=(
        "ls -la"
        "git status"
        "pip install requests"
        "SELECT * FROM users WHERE id = 1"
    )

    for cmd in "${safe_commands[@]}"; do
        if bash "${HOOKS_DIR}/03_block_dangerous.sh" "${cmd}" 2>&1; then
            pass "Correctly allowed: ${cmd:0:50}"
        else
            fail "Safe command was blocked: ${cmd}"
        fi
    done
}

# ---- Test: 04_wip_safety.sh -----------------------------------------------

test_wip_safety() {
    echo ""
    echo "--- Test: 04_wip_safety.sh ---"

    # Init a temporary git repo
    local git_test_dir="${TEST_DIR}/git_test"
    mkdir -p "${git_test_dir}"
    cd "${git_test_dir}"
    git init --quiet
    git config user.email "test@hooks.dev"
    git config user.name "Hook Test"
    echo "initial" > file.txt
    git add file.txt
    git commit --quiet -m "Initial commit"

    # Clean working tree — should skip
    local output_clean
    output_clean="$(bash "${HOOKS_DIR}/04_wip_safety.sh" 2>&1 || true)"
    if echo "${output_clean}" | grep -q "stash"; then
        fail "Should not stash when working tree is clean"
    else
        pass "Clean working tree correctly skipped"
    fi

    # Dirty working tree — should stash
    echo "dirty" >> file.txt

    local output_dirty
    output_dirty="$(bash "${HOOKS_DIR}/04_wip_safety.sh" 2>&1 || true)"
    if echo "${output_dirty}" | grep -iq "stash"; then
        pass "Dirty working tree stashed correctly"
    else
        fail "Dirty working tree was not stashed"
        echo "       Output: ${output_dirty}"
    fi

    # Verify stash was created
    local stash_count
    stash_count="$(git stash list 2>/dev/null | grep -c "WIP/CLAUDE_CODE" || true)"
    if [[ "${stash_count}" -ge 1 ]]; then
        pass "Stash created with WIP prefix (count=${stash_count})"
    else
        fail "No WIP stash found in git stash list"
    fi

    # Clean up the stash for this test
    git stash drop --quiet 2>/dev/null || true

    cd "${TEST_DIR}"
}

# ---- Main ------------------------------------------------------------------

main() {
    echo "============================================"
    echo "  Claude Code Hooks — Test Suite"
    echo "============================================"
    echo ""

    trap teardown EXIT
    setup

    test_format_on_write
    test_audit_trail
    test_block_dangerous
    test_wip_safety

    echo ""
    echo "============================================"
    echo -e "  Results: ${GREEN}${PASS_COUNT} passed${NC}, ${RED}${FAIL_COUNT} failed${NC}"
    echo "============================================"

    if [[ "${FAIL_COUNT}" -gt 0 ]]; then
        exit 1
    fi
}

main
