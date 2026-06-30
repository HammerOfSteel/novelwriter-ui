// update.js — pull latest code, rebuild, and restart the server
module.exports = {
  run: [
    {
      method: "shell.run",
      params: {
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
    },
    // Stop the running server (if any) and restart it so new code takes effect
    {
      method: "script.stop",
      params: {
        uri: "start.js"
      }
    },
    {
      method: "script.start",
      params: {
        uri: "start.js"
      }
    }
  ]
}
