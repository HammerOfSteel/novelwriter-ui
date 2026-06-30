// install.js — run once to set up the environment
module.exports = {
  run: [
    // 1. Init git submodule (the NovelWriter engine)
    {
      method: "shell.run",
      params: {
        message: "git submodule update --init --recursive",
        path: "."
      }
    },
    // 2. Create Python 3.11 virtual environment with uv
    {
      method: "shell.run",
      params: {
        message: "uv venv env --python 3.11",
        path: "."
      }
    },
    // 3. Install Python backend dependencies
    {
      method: "shell.run",
      params: {
        venv: "env",
        message: "uv pip install -r requirements.txt",
        path: "."
      }
    },
    // 4. Install Node.js frontend dependencies
    {
      method: "shell.run",
      params: {
        message: "npm install",
        path: "frontend"
      }
    },
    // 5. Build the SvelteKit frontend
    {
      method: "shell.run",
      params: {
        message: "npm run build",
        path: "frontend"
      }
    }
  ]
}
