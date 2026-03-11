return {
  {
    "lervag/vimtex",
    ft = { "tex" }, -- THIS is the key line
    init = function()
      vim.g.vimtex_view_method = "zathura"
      vim.g.vimtex_compiler_method = "latexmk"
    end,
  },
}
