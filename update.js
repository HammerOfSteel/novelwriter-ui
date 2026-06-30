// update.js — pull latest code and rebuild
module.exports = {
  run: [
    {
      method: "shell.run",
      params: {
        message: "git pull",
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
