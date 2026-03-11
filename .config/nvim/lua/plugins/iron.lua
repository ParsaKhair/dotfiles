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
        repl_open_cmd = require("iron.view").bottom(40),
      },
      -- Iron keymaps
      keymaps = {
        send_motion = "<space>sc",
        visual_send = "<space>sc",
        send_file = "<space>sf",
        send_line = "<space>sl",
        send_paragraph = "<space>sp",
        send_until_cursor = "<space>su",
        send_mark = "<space>sm",
        mark_motion = "<space>mc",
        mark_visual = "<space>mc",
        remove_mark = "<space>md",
        cr = "<space>s<cr>",
        interrupt = "<space>s<space>",
        exit = "<space>sq",
        clear = "<space>cl",
      },
      -- If the highlight is on, you can change how it looks
      highlight = { italic = true },
      ignore_blank_lines = true,
    })
  end,
}
