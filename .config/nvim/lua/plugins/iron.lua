return {
  "Vigemus/iron.nvim",
  config = function()
    local iron = require("iron.core")

    iron.setup({
      config = {
        -- Whether a repl should be discarded or not
        scratch_repl = true,
        -- Your repl definitions come here
        repl_definition = {
          sh = { command = { "bash" } },
          python = {
            -- Use `ipython` if available, fallback to `python3`
            command = function()
              local ipython = vim.fn.exepath("ipython3")
              if ipython ~= "" then
                return { ipython }
              else
                return { "python3" }
              end
            end,
          },
        },
        -- How the repl window will be displayed
        repl_open_cmd = require("iron.view").right(40),
      },
      -- Iron keymaps
      keymaps = {
        send_motion = "\\sc",
        visual_send = "\\sc",
        send_file = "\\sf",
        send_line = "\\sl",
        send_paragraph = "\\sp",
        send_until_cursor = "\\su",
        send_mark = "\\sm",
        mark_motion = "\\mc",
        mark_visual = "\\mc",
        remove_mark = "\\md",
        cr = "\\s<cr>",
        interrupt = "\\s<space>",
        exit = "\\sq",
        clear = "\\cl",
      },
      -- If the highlight is on, you can change how it looks
      highlight = { italic = true },
      ignore_blank_lines = true,
    })
  end,
}
