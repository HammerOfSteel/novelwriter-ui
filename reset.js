// reset.js — remove venv and frontend build, keep all user project data
module.exports = {
  run: [
    {
      method: "shell.run",
      params: {
        // Remove the Python virtual environment and the compiled frontend
        // User novel projects (~/NovelWriter/*) are NOT touched
        message: "rm -rf env frontend/build frontend/.svelte-kit frontend/node_modules",
        path: "."
      }
    }
  ]
}
