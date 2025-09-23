-- bootstrap lazy.nvim, LazyVim and your plugins
require("config.lazy")
-- Exit insert mode by typing 'jk'
vim.api.nvim_set_keymap("i", "jk", "<Esc>", { noremap = true, silent = true })

-- Exit visual mode by typing 'jk'
vim.api.nvim_set_keymap("v", "jk", "<Esc>", { noremap = true, silent = true })
