// update.js — pull latest code and rebuild
module.exports = {
  run: [
    {
      method: "shell.run",
      params: {
        // Use explicit remote/branch to avoid "no tracking info" errors
        message: "git pull origin main",
        path: "."
      }
    },
    {
      method: "shell.run",
      params: {
        message: "git submodule update --remote --merge",
        path: "."
      }
    },
    {
      method: "shell.run",
      params: {
        venv: "env",
        // Unset any stale VIRTUAL_ENV from a previous bad install
        env: { VIRTUAL_ENV: "" },
        message: "uv pip install -r requirements.txt",
        path: "."
      }
    },
    {
      method: "shell.run",
      params: {
        message: "npm install && npm run build",
        path: "frontend"
      }
    }
  ]
}
