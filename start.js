module.exports = {
  daemon: true,
  run: [
    {
      method: "shell.run",
      params: {
        venv: "env",
        path: ".",
        env: {
          PYTHONPATH: "."
        },
        message: [
          "uvicorn backend.server:app --host 127.0.0.1 --port {{port}}"
        ],
        on: [{
          event: "/http:\\/\\/[0-9.:]+/",
          done: true
        }]
      }
    },
    {
      method: "local.set",
      params: {
        url: "{{input.event[0]}}"
      }
    }
  ]
}
