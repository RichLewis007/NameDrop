#!/usr/bin/env bash
# Development menu script for NameDrop
#
# Author: Rich Lewis
# GitHub: @RichLewis007

set -uo pipefail

# ------------------------------------------------------------
# UI Functions (self-contained, no external dependencies)
# ------------------------------------------------------------

# Logging functions
log_info() {
  echo "ℹ  $*" >&2
}

log_error() {
  echo "✗ ERROR: $*" >&2
}

log_warn() {
  echo "⚠  WARNING: $*" >&2
}

log_ok() {
  echo "✓ $*" >&2
}

# Confirm function - prompts user for yes/no
confirm() {
  local prompt="$1"
  local response
  while true; do
    printf "%s" "$prompt" >&2
    read -r response
    case "$response" in
      [yY]|[yY][eE][sS]) return 0 ;;
      [nN]|[nN][oO]|"") return 1 ;;
      *) echo "Please answer yes or no." >&2 ;;
    esac
  done
}

# Command detection helpers
_ui_have_cmd() {
  command -v "$1" >/dev/null 2>&1
}

_ui_have_gum() { _ui_have_cmd gum; }
_ui_have_fzf() { _ui_have_cmd fzf; }

# gum and fzf menus
_ui_menu_gum() {
  local header="$1"; shift
  local prompt_line="$1"; shift
  local options=("$@")

  local combined_header
  if [[ -n "$prompt_line" && "$prompt_line" != "$header" ]]; then
    combined_header="${header}\n${prompt_line}"
  else
    combined_header="$header"
  fi

  # Use -- so options starting with "-" are not treated as flags
  gum choose --header "$combined_header" -- "${options[@]}"
}

_ui_menu_fzf() {
  local header="$1"; shift
  local prompt_line="$1"; shift
  local options=("$@")

  local fzf_header="$header"
  local fzf_prompt="$prompt_line"
  if [[ -z "$fzf_prompt" ]]; then
    fzf_prompt="$fzf_header"
  fi

  printf "%s\n" "${options[@]}" | fzf \
    --header="$fzf_header" \
    --prompt="${fzf_prompt} " \
    --height=100% \
    --border \
    --reverse \
    --info=hidden
}

# Basic numbered menu (fallback)
menu_basic() {
  local prompt="$1"; shift
  local options=("$@")
  local count=${#options[@]}
  local i choice
  local border="============================================================"

  if (( count == 0 )); then
    log_error "menu_basic called with no options"
    return 1
  fi

  while true; do
    printf "\n%s\n" "$border"
    printf "%s\n" "$prompt"
    printf "%s\n" "$border"
    for i in "${!options[@]}"; do
      printf "  %2d) %s\n" "$((i+1))" "${options[$i]}"
    done
    printf "  q) Quit\n"
    printf "%s\n" "$border"

    printf "\nChoose: "
    if ! read -r choice; then
      log_warn "EOF on input, exiting menu."
      return 1
    fi

    case "$choice" in
      q|Q) return 1 ;;
      ''|*[!0-9]*) log_warn "Please enter a number or q."; continue ;;
    esac

    if (( choice >= 1 && choice <= count )); then
      REPLY=$((choice-1))
      return 0
    else
      log_warn "Invalid choice."
    fi
  done
}

# Pick option - interactive menu selection with fzf/gum/basic fallback
pick_option() {
  local prompt="$1"; shift
  local options=("$@")
  local choice

  if (( ${#options[@]} == 0 )); then
    log_error "pick_option called with no options"
    return 1
  fi

  # Split into header and prompt_line on first newline
  local header prompt_line
  header="${prompt%%$'\n'*}"
  if [[ "$prompt" == *$'\n'* ]]; then
    prompt_line="${prompt#*$'\n'}"
  else
    prompt_line="$prompt"
  fi

  # Prefer fzf for fuzzy type-to-search menus
  if _ui_have_fzf; then
    choice=$(_ui_menu_fzf "$header" "$prompt_line" "${options[@]}") || return 1
    printf "%s\n" "$choice"
    return 0
  fi

  # Fallback to gum if available (arrow navigation, no fuzzy search)
  if _ui_have_gum; then
    choice=$(_ui_menu_gum "$header" "$prompt_line" "${options[@]}") || return 1
    printf "%s\n" "$choice"
    return 0
  fi

  # Finally, basic numbered menu with border
  if menu_basic "$prompt" "${options[@]}"; then
    printf "%s\n" "${options[$REPLY]}"
    return 0
  else
    return 1
  fi
}

# Run command with spinner
run_with_spinner() {
  local message="$1"
  shift
  local cmd=("$@")
  
  # Simple spinner implementation
  local spinner_chars="|/-\\"
  local pid
  local spinner_pid
  
  # Start the command in background
  "${cmd[@]}" >/dev/null 2>&1 &
  pid=$!
  
  # Show spinner while command runs
  (
    local i=0
    while kill -0 "$pid" 2>/dev/null; do
      printf "\r%s %s" "$message" "${spinner_chars:$i:1}" >&2
      sleep 0.1
      i=$(( (i + 1) % 4 ))
    done
    printf "\r%s done\n" "$message" >&2
  ) &
  spinner_pid=$!
  
  # Wait for command to complete
  wait "$pid"
  local exit_code=$?
  
  # Stop spinner
  kill "$spinner_pid" 2>/dev/null || true
  wait "$spinner_pid" 2>/dev/null || true
  
  return $exit_code
}

# Get the script directory (project root)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Menu handler functions
run_app() {
  log_info "Running NameDrop application..."
  uv run python main.py
}

check_code() {
  log_info "Checking code with ruff..."
  if command -v ruff >/dev/null 2>&1; then
    run_with_spinner "Running ruff check" ruff check . || true
  else
    log_warn "ruff not found. Running via uv..."
    run_with_spinner "Running ruff check" uv run ruff check . || true
  fi
}

check_format() {
  log_info "Checking code formatting (no changes)..."
  if command -v ruff >/dev/null 2>&1; then
    run_with_spinner "Running ruff format check" ruff format --check . || true
  else
    log_warn "ruff not found. Running via uv..."
    run_with_spinner "Running ruff format check" uv run ruff format --check . || true
  fi
}

format_code() {
  log_info "Formatting code with ruff..."
  if command -v ruff >/dev/null 2>&1; then
    run_with_spinner "Running ruff format" ruff format .
    log_ok "Code formatted successfully"
  else
    log_warn "ruff not found. Running via uv..."
    run_with_spinner "Running ruff format" uv run ruff format .
    log_ok "Code formatted successfully"
  fi
}

sync_deps() {
  log_info "Syncing dependencies with uv..."
  run_with_spinner "Running uv sync" uv sync
}

run_tests() {
  log_info "Running tests..."
  if command -v pytest >/dev/null 2>&1; then
    run_with_spinner "Running pytest" pytest -v || true
  elif uv run pytest --version >/dev/null 2>&1; then
    run_with_spinner "Running pytest via uv" uv run pytest -v || true
  else
    log_warn "No tests found or pytest not available"
    if confirm "Would you like to install pytest? [y/N] "; then
      run_with_spinner "Installing pytest" uv add --dev pytest
      run_with_spinner "Running pytest" uv run pytest -v || true
    fi
  fi
}

clean_cache() {
  log_info "Finding Python cache files and directories..."
  
  # Collect directories and files to delete
  local cache_dirs
  local pyc_files
  local pyo_files
  
  cache_dirs=$(find . -type d -name "__pycache__" 2>/dev/null | sort)
  pyc_files=$(find . -type f -name "*.pyc" 2>/dev/null | sort)
  pyo_files=$(find . -type f -name "*.pyo" 2>/dev/null | sort)
  
  # Count items
  local dir_count=0
  local pyc_count=0
  local pyo_count=0
  
  if [[ -n "$cache_dirs" ]]; then
    dir_count=$(echo "$cache_dirs" | wc -l | tr -d ' ')
  fi
  if [[ -n "$pyc_files" ]]; then
    pyc_count=$(echo "$pyc_files" | wc -l | tr -d ' ')
  fi
  if [[ -n "$pyo_files" ]]; then
    pyo_count=$(echo "$pyo_files" | wc -l | tr -d ' ')
  fi
  
  local total=$((dir_count + pyc_count + pyo_count))
  
  if [[ $total -eq 0 ]]; then
    log_ok "No cache files or directories found"
    return 0
  fi
  
  # Display what will be deleted
  echo ""
  log_info "The following will be deleted:"
  echo ""
  
  if [[ $dir_count -gt 0 ]]; then
    echo "  Directories (__pycache__): $dir_count"
    echo "$cache_dirs" | sed 's/^/    /'
    echo ""
  fi
  
  if [[ $pyc_count -gt 0 ]]; then
    echo "  Files (*.pyc): $pyc_count"
    echo "$pyc_files" | sed 's/^/    /'
    echo ""
  fi
  
  if [[ $pyo_count -gt 0 ]]; then
    echo "  Files (*.pyo): $pyo_count"
    echo "$pyo_files" | sed 's/^/    /'
    echo ""
  fi
  
  # Prompt for confirmation
  if ! confirm "Delete these cache files and directories? [y/N] "; then
    log_info "Cache cleanup cancelled"
    return 0
  fi
  
  # Delete the items
  log_info "Deleting cache files and directories..."
  if [[ -n "$cache_dirs" ]]; then
    echo "$cache_dirs" | xargs rm -rf 2>/dev/null || true
  fi
  if [[ -n "$pyc_files" ]]; then
    echo "$pyc_files" | xargs rm -f 2>/dev/null || true
  fi
  if [[ -n "$pyo_files" ]]; then
    echo "$pyo_files" | xargs rm -f 2>/dev/null || true
  fi
  
  log_ok "Cache cleaned"
}

remove_venv() {
  log_info "Checking for virtual environment..."
  
  local venv_paths=()
  
  # Check for common venv directory names
  if [[ -d ".venv" ]]; then
    venv_paths+=(".venv")
  fi
  if [[ -d "venv" ]]; then
    venv_paths+=("venv")
  fi
  if [[ -d "env" ]]; then
    venv_paths+=("env")
  fi
  if [[ -d ".env" ]]; then
    venv_paths+=(".env")
  fi
  
  if [[ ${#venv_paths[@]} -eq 0 ]]; then
    log_ok "No virtual environment directory found"
    return 0
  fi
  
  # Display what will be deleted
  echo ""
  log_info "The following virtual environment directories will be deleted:"
  echo ""
  for venv in "${venv_paths[@]}"; do
    local size=""
    if command -v du >/dev/null 2>&1; then
      size=$(du -sh "$venv" 2>/dev/null | cut -f1)
      echo "  $venv ($size)"
    else
      echo "  $venv"
    fi
  done
  echo ""
  log_warn "This will require running 'uv sync' to recreate the environment"
  echo ""
  
  # Prompt for confirmation
  if ! confirm "Delete these virtual environment directories? [y/N] "; then
    log_info "Virtual environment removal cancelled"
    return 0
  fi
  
  # Delete the directories
  log_info "Removing virtual environment directories..."
  for venv in "${venv_paths[@]}"; do
    if rm -rf "$venv" 2>/dev/null; then
      log_ok "Removed $venv"
    else
      log_error "Failed to remove $venv"
    fi
  done
  
  echo ""
  if confirm "Would you like to recreate the virtual environment now? [y/N] "; then
    log_info "Recreating virtual environment..."
    run_with_spinner "Running uv sync" uv sync
    log_ok "Virtual environment recreated"
  else
    log_info "Run 'uv sync' to recreate the virtual environment when ready"
  fi
}

show_project_info() {
  log_info "Project Information:"
  echo ""
  echo "  Project: NameDrop"
  echo "  Location: $SCRIPT_DIR"
  echo ""
  # Get Python version from uv (the version the app uses)
  local python_executable
  python_executable=$(uv python find 2>/dev/null)
  if [[ -n "$python_executable" && -x "$python_executable" ]]; then
    echo "  Python version: $("$python_executable" --version 2>&1)"
  else
    echo "  Python version: Not available (run 'uv sync' to set up the environment)"
  fi
  echo "  uv version: $(uv --version 2>&1 || echo 'Not available')"
  echo ""
  if [ -f "pyproject.toml" ]; then
    echo "  Project version: $(grep '^version' pyproject.toml | cut -d'"' -f2 || echo 'Not found')"
  fi
  echo ""
}

install_deps() {
  log_info "Installing dependencies..."
  run_with_spinner "Running uv sync" uv sync
}

type_check() {
  log_info "Running type check with mypy..."
  if command -v mypy >/dev/null 2>&1; then
    run_with_spinner "Running mypy" mypy . --ignore-missing-imports || true
  elif uv run mypy --version >/dev/null 2>&1; then
    run_with_spinner "Running mypy via uv" uv run mypy . --ignore-missing-imports || true
  else
    log_warn "mypy not found"
    if confirm "Would you like to install mypy? [y/N] "; then
      run_with_spinner "Installing mypy" uv add --dev mypy
      run_with_spinner "Running mypy" uv run mypy . --ignore-missing-imports || true
    fi
  fi
}

# Main menu
main() {
  while true; do
    choice=$(pick_option "NameDrop Development Menu
Choose an action:" \
      "Run" \
      "Check (lint)" \
      "Check format" \
      "Format code" \
      "Sync dependencies" \
      "Install dependencies" \
      "Test" \
      "Type check (mypy)" \
      "Clean cache" \
      "Remove virtual environment" \
      "Project info" \
      "Quit") || exit 0

    case "$choice" in
      "Run")
        run_app
        ;;
      "Check (lint)")
        check_code
        ;;
      "Check format")
        check_format
        ;;
      "Format code")
        format_code
        ;;
      "Sync dependencies")
        sync_deps
        ;;
      "Install dependencies")
        install_deps
        ;;
      "Test")
        run_tests
        ;;
      "Type check (mypy)")
        type_check
        ;;
      "Clean cache")
        clean_cache
        ;;
      "Remove virtual environment")
        remove_venv
        ;;
      "Project info")
        show_project_info
        ;;
      "Quit")
        log_info "Goodbye!"
        exit 0
        ;;
      *)
        log_error "Unknown choice: $choice"
        ;;
    esac

    echo ""
    read -p "Press Enter to return to menu (Ctrl+C to exit)..."
    echo ""
  done
}

# Run main menu
main

