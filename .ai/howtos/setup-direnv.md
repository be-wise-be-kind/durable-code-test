# Setup direnv for Automatic Environment Variables

**Purpose**: Configure direnv to automatically load environment variables when entering the project directory
**Scope**: Development environment setup for secure token and configuration management

---

## Overview

direnv is a shell extension that automatically loads and unloads environment variables based on the current directory. This guide explains how to set up direnv for the project, ensuring GitHub tokens and other sensitive configuration are automatically available without manual exports.

## Prerequisites

- Unix-like operating system (Linux, macOS)
- Bash, Zsh, or Fish shell
- Git repository with `.env` file for sensitive configuration

## Installation

### macOS (using Homebrew)
```bash
brew install direnv
```

### Ubuntu/Debian
```bash
sudo apt-get update
sudo apt-get install direnv
```

### Manual Installation
```bash
# Download the latest release
curl -sfL https://direnv.net/install.sh | bash

# Move to your bin directory
mv direnv ~/bin/
chmod +x ~/bin/direnv
```

## Shell Integration

Add the appropriate hook to your shell configuration file:

### Bash (~/.bashrc)
```bash
eval "$(direnv hook bash)"
```

### Zsh (~/.zshrc)
```bash
eval "$(direnv hook zsh)"
```

### Fish (~/.config/fish/config.fish)
```fish
direnv hook fish | source
```

After adding the hook, reload your shell:
```bash
source ~/.bashrc  # or ~/.zshrc for Zsh
```

## Project Configuration

### 1. Create .envrc File

Create a `.envrc` file in the project root:

```bash
cat > .envrc << 'EOF'
# Load environment variables from .env file
if [ -f .env ]; then
  source .env
  # Export all loaded variables
  export GITHUB_TOKEN
  export CLAUDE_API_KEY
  # Add other variables as needed
fi
EOF
```

### 2. Create .env File

Create a `.env` file with your actual tokens:

```bash
cat > .env << 'EOF'
# GitHub CLI Configuration
GITHUB_TOKEN=your-github-personal-access-token-here

# Claude API Configuration
CLAUDE_API_KEY=your-claude-api-key-here

# Other project-specific variables
DATABASE_URL=postgresql://user:password@localhost/dbname
EOF
```

### 3. Create .env.example

Provide a template for other developers:

```bash
cat > .env.example << 'EOF'
# GitHub CLI Configuration
GITHUB_TOKEN=your-github-personal-access-token-here

# Claude API Configuration
CLAUDE_API_KEY=your-claude-api-key-here

# Database Configuration
DATABASE_URL=postgresql://user:password@localhost/dbname
EOF
```

### 4. Update .gitignore

Ensure sensitive files are not committed:

```bash
echo ".env" >> .gitignore
echo ".envrc.local" >> .gitignore
# Note: .envrc can be committed as it doesn't contain secrets
```

## Activation

### Allow direnv for the Project

When you first enter a project directory with a `.envrc` file, direnv will block it for security. You must explicitly allow it:

```bash
cd /path/to/project
direnv allow
```

You'll see output like:
```
direnv: loading .envrc
direnv: export +GITHUB_TOKEN +CLAUDE_API_KEY
```

### Verify Configuration

Test that environment variables are loaded:

```bash
# Check if variables are set
echo "GITHUB_TOKEN is set: ${GITHUB_TOKEN:+Yes}"

# Test GitHub CLI authentication
gh auth status

# Test other integrations
env | grep GITHUB_TOKEN
```

## Security Best Practices

### 1. Never Commit Secrets
- Always keep `.env` in `.gitignore`
- Use `.env.example` to show required variables without values
- Review commits before pushing to ensure no tokens are included

### 2. Restrict .env Permissions
```bash
# Make .env readable only by owner
chmod 600 .env
```

### 3. Use Different Tokens per Environment
- Development: Limited scope tokens
- Production: Separate tokens with appropriate permissions
- CI/CD: Dedicated tokens with minimal required permissions

### 4. Rotate Tokens Regularly
- Set calendar reminders to rotate tokens
- Update `.env` when tokens change
- Run `direnv reload` after updates

## Common Commands

### Reload Environment
```bash
direnv reload
```

### Temporarily Disable direnv
```bash
direnv deny
```

### Re-enable direnv
```bash
direnv allow
```

### Check direnv Status
```bash
direnv status
```

### Edit and Auto-reload
```bash
direnv edit
# Opens .envrc in editor and reloads on save
```

## Troubleshooting

### Problem: "direnv: command not found"
**Solution**: Ensure direnv is in your PATH:
```bash
export PATH="$HOME/bin:$PATH"
```

### Problem: Variables Not Loading
**Solution**: Check if direnv is allowed:
```bash
direnv allow
```

### Problem: GitHub CLI Not Finding Token
**Solution**: Ensure GITHUB_TOKEN is exported:
```bash
# In .envrc
export GITHUB_TOKEN
```

### Problem: Changes to .env Not Reflected
**Solution**: Reload direnv after editing .env:
```bash
direnv reload
```

### Problem: Shell Hook Not Working
**Solution**: Verify hook is properly installed:
```bash
# Check if hook is active
direnv version
# Should show version if properly configured
```

## Integration with Development Workflow

### GitHub CLI Operations
With direnv configured, GitHub CLI commands work seamlessly:
```bash
gh pr create  # Uses GITHUB_TOKEN automatically
gh pr list
gh issue create
```

### Docker Compose
Environment variables are available for Docker:
```bash
docker-compose up  # Uses vars from .env
```

### Make Targets
Make commands have access to environment:
```bash
make deploy  # Can use $GITHUB_TOKEN
```

## Advanced Configuration

### Project-specific Python Virtual Environment
Add to `.envrc`:
```bash
# Activate Python virtual environment
if [ -f .venv/bin/activate ]; then
  source .venv/bin/activate
fi
```

### Node Version Management
Add to `.envrc`:
```bash
# Use specific Node version
use_nvm() {
  local node_version="$(cat .nvmrc)"
  nvm use "$node_version"
}
use_nvm
```

### Custom Functions
Add project-specific functions to `.envrc`:
```bash
# Custom project commands
project_test() {
  make test-all
}
export -f project_test
```

## Benefits

1. **Automatic Loading**: No need to manually source files
2. **Project Isolation**: Variables are scoped to project directory
3. **Security**: Explicit approval required for each `.envrc`
4. **Team Consistency**: Shared `.envrc` ensures consistent setup
5. **CI/CD Compatibility**: Same variable names in development and production

## Related Documentation

- [Setup Development](setup-development.md) - Complete development environment setup
- [GitHub Merge Workflow](github-merge-workflow.md) - Using GitHub CLI with tokens
- [Debug Issues](debug-issues.md) - Troubleshooting environment problems

## Summary

direnv simplifies environment management by automatically loading project-specific variables. Once configured, you'll never need to manually export tokens or remember to source configuration files. The setup ensures security through explicit approval and keeps sensitive data out of version control while maintaining a smooth development workflow.
