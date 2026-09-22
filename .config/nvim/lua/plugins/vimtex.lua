return {
  {
    "lervag/vimtex",
    lazy = false,
    ft = "tex",
    init = function()
      vim.g.vimtex_view_method = "zathura"
      vim.g.vimtex_compiler_method = "latexmk"
      vim.g.vimtex_version_check = 0
    end,
  },
}
