# Power of Hooks — Lifecycle Automation for Agentic Workflows

Claude Code hooks are **shell commands that fire at specific lifecycle events** during a session. They let you inject custom behaviour before or after file operations, commands, and session lifecycle transitions — without modifying Claude Code itself.

## Hook Lifecycle

```
Session Start
    |
    v
  beforeRead  ──►  Read file  ──►  afterRead
    |
    v
  beforeEdit  ──►  Edit file  ──►  afterEdit
    |
    v
  beforeWrite ──►  Write file  ──►  afterWrite
    |
    v
  beforeCommand ─►  Run command ──►  afterCommand
    |
    v
  preExit  ──►  Session End
```

## The 10 Hooks

| Hook | Trigger | Common Use Case |
|---|---|---|
| `beforeRead` | Before reading a file from disk | Refresh stale cache, check file permissions |
| `afterRead` | After reading a file from disk | Log file accesses, annotate content |
| `beforeEdit` | Before applying an edit to a file | Validate edit permissions, backup original |
| `afterEdit` | After applying an edit to a file | Lint the result, track changes |
| `beforeWrite` | Before writing a file to disk | Template injection, secret scanning |
| `afterWrite` | After writing a file to disk | Auto-format, compile, trigger rebuilds |
| `beforeCommand` | Before executing a shell command | Block dangerous commands, inject env vars |
| `afterCommand` | After executing a shell command | Audit logging, collect metrics |
| `preExit` | When the session is ending | Stash WIP, clean temp files, send notifications |
| `preToolUse` | Before any tool is invoked | Rate limiting, telemetry, approvals |

## Project Structure

```
18_power_of_hooks/
  index.html         — Explainer page with Mermaid diagrams
  hooks/
    01_format_on_write.sh   — afterWrite: auto-format Python files
    02_audit_trail.sh       — afterCommand: log every command
    03_block_dangerous.sh   — beforeCommand: block dangerous commands
    04_wip_safety.sh        — preExit: auto-stash WIP changes
  config_example/
    settings.json   — Hook configuration snippet
  test_hooks.sh     — Test suite for all hooks
  README.md         — This file
```

## Quick Start

### 1. Copy the hooks into your project

```bash
cp -r hooks/ your-project/.claude/hooks/
chmod +x your-project/.claude/hooks/*.sh
```

### 2. Configure hooks in `settings.local.json`

```json
{
  "hooks": {
    "afterWrite": ".claude/hooks/01_format_on_write.sh '{file}'",
    "beforeCommand": ".claude/hooks/03_block_dangerous.sh '{command}'",
    "afterCommand": ".claude/hooks/02_audit_trail.sh '{command}' {exit_code}",
    "preExit": ".claude/hooks/04_wip_safety.sh"
  }
}
```

### 3. Run the tests

```bash
bash test_hooks.sh
```

## Hook Principles

**When to use a hook:**
- You want to enforce a policy (formatting, security, audit) transparently
- The behaviour is synchronous and should block/allow the parent operation
- The logic is simple enough for a shell script (< ~200 lines)

**When NOT to use a hook:**
- Long-running background tasks (use a CLI workflow or skill instead)
- Complex multi-step workflows (use a workflow orchestration tool)
- Interactive user-facing features (use a slash command skill)

## Variable Reference

Hooks receive context via variables passed as arguments:

| Variable | Description | Available In |
|---|---|---|
| `{file}` | Absolute path of the file being read/written/edited | beforeRead, afterRead, beforeWrite, afterWrite, beforeEdit, afterEdit |
| `{command}` | The shell command being executed | beforeCommand, afterCommand |
| `{exit_code}` | Exit code of the last command (int) | afterCommand |
| `{tool_name}` | Name of the MCP/Built-in tool being invoked | preToolUse |
| `{tool_input}` | JSON input for the tool being invoked | preToolUse |

## License

This project is part of the AI Adoption Projects collection — free to use and modify.
