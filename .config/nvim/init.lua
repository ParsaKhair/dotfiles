-- bootstrap lazy.nvim, LazyVim and your plugins
require("config.lazy")
require("lazy").setup("plugins")
vim.keymap.set("i", "jk", "<Esc>")
