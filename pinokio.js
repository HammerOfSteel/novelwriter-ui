module.exports = {
  version: "7.0",
  title: "NovelWriter UI",
  description: "AI-assisted novel writing powered by Ollama",
  icon: "icon.png",
  menu: async (kernel, info) => {
    const installed = info.exists("env")

    const running = {
      install: info.running("install.js"),
      start:   info.running("start.js"),
      update:  info.running("update.js"),
      reset:   info.running("reset.js"),
    }

    if (running.install) {
      return [{
        default: true,
        icon: "fa-solid fa-plug",
        text: "Installing...",
        href: "install.js",
      }]
    }

    if (!installed) {
      return [{
        default: true,
        icon: "fa-solid fa-download",
        text: "Install",
        href: "install.js",
      }]
    }

    if (running.update) {
      return [{
        default: true,
        icon: "fa-solid fa-arrows-rotate",
        text: "Updating...",
        href: "update.js",
      }]
    }

    if (running.reset) {
      return [{
        default: true,
        icon: "fa-solid fa-trash",
        text: "Resetting...",
        href: "reset.js",
      }]
    }

    if (running.start) {
      const local = info.local("start.js")
      if (local && local.url) {
        return [{
          default: true,
          icon: "fa-solid fa-book-open",
          text: "Open NovelWriter",
          href: local.url,
        }, {
          icon: "fa-solid fa-terminal",
          text: "Terminal",
          href: "start.js",
        }, {
          icon: "fa-solid fa-arrows-rotate",
          text: "Update",
          href: "update.js",
        }, {
          icon: "fa-regular fa-circle-xmark",
          text: "Reset",
          href: "reset.js",
        }]
      }
      return [{
        default: true,
        icon: "fa-solid fa-terminal",
        text: "Terminal",
        href: "start.js",
      }]
    }

    return [{
      default: true,
      icon: "fa-solid fa-play",
      text: "Start",
      href: "start.js",
    }, {
      icon: "fa-solid fa-arrows-rotate",
      text: "Update",
      href: "update.js",
    }, {
      icon: "fa-solid fa-download",
      text: "Re-install",
      href: "install.js",
    }, {
      icon: "fa-regular fa-circle-xmark",
      text: "Reset",
      href: "reset.js",
    }]
  }
}
