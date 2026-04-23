-- if true then return {} end -- WARN: REMOVE THIS LINE TO ACTIVATE THIS FILE

-- AstroCore provides a central place to modify mappings, vim options, autocommands, and more!
-- Configuration documentation can be found with `:h astrocore`
-- NOTE: We highly recommend setting up the Lua Language Server
-- NOTE: `:LspInstall lua_ls`
-- NOTE: `:LspInstall python`
--       as this provides autocomplete and documentation while editing

---@type LazySpec
return {
  "AstroNvim/astrocore",
  ---@type AstroCoreOpts
  opts = {
    -- Configure core features of AstroNvim
    features = {
      large_buf = { size = 1024 * 256, lines = 10000 }, -- set global limits for large files for disabling features like treesitter
      autopairs = true, -- enable autopairs at start
      cmp = true, -- enable completion at start
      diagnostics_mode = 3, -- diagnostic mode on start (0 = off, 1 = no signs/virtual text, 2 = no virtual text, 3 = on)
      highlighturl = true, -- highlight URLs at start
      notifications = true, -- enable notifications at start
    },
    -- Diagnostics configuration (for vim.diagnostics.config({...})) when diagnostics are on
    diagnostics = {
      virtual_text = true,
      underline = true,
    },
    -- vim options can be configured here
    options = {
      opt = { -- vim.opt.<key>
        relativenumber = true, -- sets vim.opt.relativenumber
        number = true, -- sets vim.opt.number
        spell = false, -- sets vim.opt.spell
        signcolumn = "yes", -- sets vim.opt.signcolumn to yes
        wrap = true, -- sets vim.opt.wrap
        swapfile = false,
        spellfile = vim.fn.stdpath("data") .. "/spell/en.utf-8.add",
      },
      g = { -- vim.g.<key>
        -- configure global vim variables (vim.g)
        -- NOTE: `mapleader` and `maplocalleader` must be set in the AstroNvim opts or before `lazy.setup`
        -- This can be found in the `lua/lazy_setup.lua` file
      },
    },
    -- Mappings can be configured through AstroCore as well.
    -- NOTE: keycodes follow the casing in the vimdocs. For example, `<Leader>` must be capitalized
    mappings = {
      -- first key is the mode
      n = {
        -- Disable below key mapppings
        ["<C-q>"] = false,
        ["<C-s>"] = false,
        ["<C-h>"] = false,
        ["<C-j>"] = false,
        ["<C-k>"] = false,
        ["<C-l>"] = false,

        -- CTRL+Mouse Srollup to increase font
        ["<C-ScrollWheelUp>"] = { "<Cmd>IncreaseFont<CR>", desc = "Increase font size" },
        ["<C-ScrollWheelDown>"] = { "<Cmd>DecreaseFont<CR>", desc = "Decrease font size" },

        -- navigate buffer tabs with `H` and `L`
        ["]b"] = false,
        ["[b"] = false,
        E = {
          function() require("astrocore.buffer").nav(vim.v.count > 0 and vim.v.count or 1) end,
          desc = "Next buffer",
        },
        Y = {
          function() require("astrocore.buffer").nav(-(vim.v.count > 0 and vim.v.count or 1)) end,
          desc = "Previous buffer",
        },

        -- better increment/decrement
        ["-"] = { "<c-x>", desc = "Descrement number" },
        ["+"] = { "<c-a>", desc = "Increment number" },

        -- Easy-Align
        ga = { "<Plug>(EasyAlign)", desc = "Easy Align" },

        -- mappings seen under group name "Buffer"
        ["<Leader>bD"] = {
          function()
            require("astroui.status.heirline").buffer_picker(
              function(bufnr) require("astrocore.buffer").close(bufnr) end
            )
          end,
          desc = "Pick to close",
        },

        -- ToggleTerm
        ["<Leader>tp"] = {
          function()
            local astro = require "astrocore"
            astro.toggle_term_cmd {
              cmd = "ipython --no-autoindent -i ~/.files/python/ipython_startup.py",
              direction = "vertical",
            }
            -- send the key stroke: "<C-\\><C-n>"
            -- vim.api.nvim_feedkeys(vim.api.nvim_replace_termcodes("<C-\\><C-n>", true, true, true), "n", true)
            -- adjust the split size to 110 using vim command : vertical resize 110
            vim.cmd "vertical resize 110"
          end,
          desc = "iPython",
        },
        -- ToggleTerm
        ["<Leader>gg"] = {
          function()
            local astro = require "astrocore"
            local worktree = astro.file_worktree()
            local flags = worktree and (" --work-tree=%s --git-dir=%s"):format(worktree.toplevel, worktree.gitdir) or ""
            astro.toggle_term_cmd { cmd = "lazygit " .. flags, direction = "float" }
          end,
          desc = "LazyGit",
        },
        ["<A-.>"] = {
          "<Cmd>ToggleTerm size=110 direction=vertical<CR>",
          desc = "ToggleTerm horizontal split",
          silent = true,
        },
        ["<A-->"] = {
          "<Cmd>ToggleTerm size=20 direction=horizontal<CR>",
          desc = "ToggleTerm horizontal split",
          silent = true,
        },

        ["<Leader>s"] = {
          function()
            -- local current_window = vim.api.nvim_get_current_win() -- save current window

            -- store the current cursor position
            -- local start_line, start_col
            -- start_line, start_col = unpack(vim.api.nvim_win_get_cursor(0))

            -- send current line to terminal
            local trim_spaces = true
            require("toggleterm").send_lines_to_terminal("single_line", trim_spaces, { args = vim.v.count })
            -- send ENTER key
            -- require("toggleterm").exec("\n", 1)

            -- Jump back with the cursor where we were at the beginning of the selection
            -- vim.api.nvim_set_current_win(current_window)
            -- vim.api.nvim_win_set_cursor(current_window, { start_line, start_col })
          end,
          desc = " Run Line at Term",
        },
        -- Replace with these for the other two options
        -- require("toggleterm").send_lines_to_terminal("visual_lines", trim_spaces, { args = vim.v.count })
        -- require("toggleterm").send_lines_to_terminal("visual_selection", trim_spaces, { args = vim.v.count })
        --

        -- tables with just a `desc` key will be registered with which-key if it's installed
        -- this is useful for naming menus
        -- ["<Leader>b"] = { desc = "Buffers" },

        -- quick save
        -- ["<C-s>"] = { ":w!<cr>", desc = "Save File" },  -- change description but the same command

        -- Disable default Ctrl-Y (scroll up) and Ctrl-E (scroll down) so they
        -- don't fire when tmux forwards C-h / C-l for pane navigation.
        ["<C-y>"] = false,
        ["<C-e>"] = false,

        ----------==================== N: MY MAPPINGS (START) ====================----------
        -- ["<Leader>n"] = { desc = " Notes" },
        -- ["<Leader>a"] = { desc = " Edit" },

        ["<Leader><cr>"] = { "<cmd>WikiJournal<cr>", desc = "Journal" },
        ["<Leader><tab>"] = { "<cmd>WikiIndex<cr>", desc = "Todo" },
        ["<Leader>`"] = { "<cmd>WikiPages<cr>", desc = "Wiki Pages" },

        -- ["<Leader><cr>"] = { "<cmd>Neorg journal today<cr>", desc = "Journal" },
        -- ["<Leader><tab>"] = { "<cmd>Neorg index<cr>", desc = "Todo" },
        -- ["<Leader>`"] = { "<cmd>WikiPages<cr>", desc = "Wiki Pages" },

        -- ["<Leader><space>"] = { "<cmd>Telescope harpoon marks<CR>", desc = "Marks list" },

        -- [","] = { "<cmd>VimwikiToggleListItem<cr>", desc = "Toggle Todo" },
        -- ["<"] = { "<cmd>TaskWikiToggle<cr><cr>", desc = "Start a Todo" },

        -- Alternate file
        -- ["<Leader>aa"] = {
        --   function()
        --     -- Get the output from the shell command
        --     local output = vim.fn.system {
        --       "python",
        --       "/lab/lib/finclab/sh/bash/vim-cmd-edit-alt-file.py",
        --       "--filepath=" .. vim.fn.expand "%:p",
        --     }
        --     vim.cmd(output)
        --   end,
        --   desc = "Switch to/from Test",
        -- },

        -- debug inside lean
        ["<Leader>dk"] = {
          function()
            -- It loads the content of `launch.json` and feed it to `dap`.
            require("dap.ext.vscode").load_launchjs()

            local f = io.open("/tmp/debugger/current_debugging_project", "r")
            if f == nil then
              vim.notify "Debugger doesn't seem to be running. (/tmp/debugger/current_debugging_project) does not exist."
            end
            local project_path = table.concat(vim.fn.readfile "/tmp/debugger/current_debugging_project")
            local lines = vim.fn.readfile(project_path .. "/.vscode/launch.json")
            local config = vim.fn.json_decode(table.concat(lines))
            print(project_path)
            print "lines..."
            print(vim.inspect(lines))
            print(vim.inspect(config["configurations"]))
            require("dap").run(config["configurations"][1])
          end,
          desc = "Debug via Lean",
        },
        ["<Leader>ds"] = {
          function()
            require("dap.ext.vscode").load_launchjs()
            require("dap").continue()
          end,
          desc = "Continue (Lean)",
        },

        -- ["<Leader>ln"] = {
        --   function()
        --     local filename = vim.fn.expand "%:t"
        --     utils.async_run(
        --       { "ts", "research", "start", "--port", "8888", "--detach", "--project", vim.fn.expand "%:p:h" },
        --       function()
        --         vim.notify("Lean research session online: http://localhost:8888/notebooks/" .. filename .. ".ipynb")
        --       end
        --     )
        --   end,
        --   desc = "Lean Research",
        -- },

        -- ["<Leader>lN"] = {
        --   function()
        --     utils.async_run({ "ts", "jupyter", "stop", "--port", "8888" }, function() end)
        --     utils.async_run(
        --       { "ts", "research", "stop", "--port", "8888" },
        --       function() vim.notify "Terminated jupyter session(s) on port 8888" end
        --     )
        --   end,
        --   desc = "Lean Research (Stop)",
        -- },

        -- ["<Leader>lb"] = {
        --   function()
        --     local folder = vim.fn.expand "%:p:h"
        --     print("Running backtest on project: " .. folder)
        --     vim.cmd "silent! write"
        --     utils.async_run({ "ts", "backtest", "--port", "60002", "--detach", "--file", vim.fn.expand "%:p",
        --     }, function()
        --       local backtest_folder = vim.fn.getqflist()[2]["text"]
        --       vim.notify("Backtest completed for: " .. backtest_folder)
        --       vim.cmd( "call timer_start(8000, { tid -> execute('e " .. backtest_folder .. "/log.txt" .. " || normal G')})")
        --     end)
        --   end,
        --   desc = "Kick-off Backtest",
        -- },

        -- ["<Leader>lJ"] = {
        --   function()
        --     local filename = vim.fn.expand "%:t"
        --     utils.async_run(
        --       { "ts", "jupyter", "start", "--port", "8888", "--detach", "--file", vim.fn.expand "%:p" },
        --       function() vim.notify("Jupyter session online: http://localhost:8888/notebooks/" .. filename .. ".ipynb") end
        --     )
        --   end,
        --   desc = "Jupyter",
        -- },

        ["<Leader>lF"] = {
          '<cmd>silent write | silent !black --exclude="__init__.py" % | autoflake -i % --expand-star-imports --remove-all-unused-imports --ignore-init-module-imports --remove-duplicate-keys --remove-unused-variables<cr>',
          desc = "Format .py",
        },
        ["<Leader>lH"] = {
          -- "<cmd>:0 | let blank=''|let t='\"\"\" {Module Name}'|put=t|put=blank|let t='id:            <your-name> (<your-email>)'|put=t|let t='last_update:   ' . strftime('%Y-%m-%d %H:%M:%S %Z')|put=t|let t='type:          lib'|put=t|let t='sensitivity:   <your-team>'|put=t|let t='platform:      any'|put=t|let t='description:   {Description}'|put=t|let t='\"\"\"'|put=t<CR>",
          --
          function()
            -- Insert a blank line at the top of the buffer
            vim.api.nvim_buf_set_lines(0, 0, 0, false, { "" })

            -- Define the header lines
            local header_lines = {
              "#!/usr/bin/env python",
              "# @Author     : <your-name>",
              "# @Email      : <your-email>",
              "# @Last Update: " .. os.date "%Y-%m-%d %H:%M:%S %Z",
              "# @Type       : lib",
              "# @Sensitivity: <your-team>",
              "# @Platform   : any",
              "",
            }
            -- Insert the header lines at the top of the buffer
            vim.api.nvim_buf_set_lines(0, 1, 1, false, header_lines)
            -- Delete the initial blank line (first line)
            vim.api.nvim_buf_set_lines(0, 0, 1, false, {})
          end,
          desc = "Add .py Header",
        },

        -- Notes
        -- ["<Leader>n<cr>"] = { "<Plug>VimwikiMakeDiaryNote", desc = "Diary (Today)", },
        -- ["<Leader>nn"] = { "<Plug>VimwikiMakeDiaryNote", desc = "Diary (Today)", },
        -- ["<Leader>ny"] = { "<Plug>VimwikiMakeYesterdayDiaryNote", desc = "Diary (Yesterday)", },
        -- ["<Leader>ne"] = { "<Plug>VimwikiTOC", desc = "Table of Contents", },
        -- ["<Leader>nc"] = { "<Plug>VimwikiColorize", desc = "Colorize", },
        -- ["<Leader>nr"] = { "<Plug>VimwikiRenameFile", desc = "Rename File", },
        -- ["<Leader>nd"] = { "<Plug>VimwikiDeleteFile", desc = "Delete File", },
        -- ["<Leader>nw"] = { "<Plug>VimwikiMakeTomorrowDiaryNote", desc = "Diary (Tomorrow)", },
        -- ["<Leader>ni"] = { "<Plug>VimwikiDiaryIndex", desc = "All Journal", },
        -- ["<Leader>nx"] = { "<Plug>VimwikiRemoveDone", desc = "Remove [x]", },
        -- ["<Leader>nt"] = { "<Plug>VimwikiNextTask", desc = "Next checkbox", },
        -- ["<Leader>ns"] = { "<CMD>call GetSyntax()<CR>", desc = "Show highlight group", },
        -- ["<Leader>np"] = { "<CMD>MarkdownPreviewToggle<CR>", desc = "Markdown Preview Toggle", },
        -- ["<Leader>nP"] = { "<CMD>MarkdownPreviewStop<CR>", desc = "Stop Markdown Preview", },

        -- Tmux move pane
        -- ["<A-h>"] = { "<cmd><C-U>TmuxNavigateLeft<cr>", desc = "Tmux navigate left" },
        -- ["<A-l>"] = { "<cmd><C-U>TmuxNavigateRight<cr>", desc = "Tmux navigate right" },
        -- ["<A-j>"] = { "<cmd><C-U>TmuxNavigateDown<cr>", desc = "Tmux navigate bottom" },
        -- ["<A-k>"] = { "<cmd><C-U>TmuxNavigateUp<cr>", desc = "Tmux navigate up" },
        -- ["<A-H>"] = { function() require("tmux").resize_left() end, desc = "Tmux resize left" },
        -- ["<A-L>"] = { function() require("tmux").resize_right() end, desc = "Tmux resize right" },
        -- ["<A-J>"] = { function() require("tmux").resize_bottom() end, desc = "Tmux resize bottom" },
        -- ["<A-K>"] = { function() require("tmux").resize_top() end, desc = "Tmux resize up" },

        -- Hop
        -- ["t"] = { "<cmd>lua require'hop'.hint_char2()<cr>", noremap = true, desc = "Hop", silent = true },

        -- Select pane
        ["<Leader>1"] = {
          function() require("astrocore.buffer").nav_to(1) end,
          desc = "Swtch to buffer 1",
        },
        ["<Leader>2"] = {
          function() require("astrocore.buffer").nav_to(2) end,
          desc = "Swtch to buffer 2",
          noremap = true,
          silent = true,
        },
        ["<Leader>3"] = {
          function() require("astrocore.buffer").nav_to(3) end,
          desc = "Swtch to buffer 3",
          noremap = true,
          silent = true,
        },

        -- Neovide fullscreen
        ["<C-F11>"] = {
          function() vim.g.neovide_fullscreen = not vim.g.neovide_fullscreen end,
          desc = "Toggle Fullscreen",
          noremap = true,
          silent = true,
        },

        -- Switch project
        ["<Leader>fp"] = { "<cmd>Telescope projects<CR>", desc = "Projects" },

        -- Neotree: filexplorer
        ["<Leader>e"] = { "<Cmd>cd %:p:h | Neotree toggle<CR>", desc = "Toggle Explorer" },

        ["<Leader>o"] = {
          function()
            if vim.bo.filetype == "neo-tree" then
              vim.cmd.wincmd "p"
            else
              vim.cmd.Neotree "focus"
            end
          end,
          desc = "Toggle Explorer Focus",
        },

        -- Set CWD
        ["<Leader>."] = { "<cmd>AstroRoot<cr>", desc = "Set CWD" },
        -- ==================== N: MY MAPPINGs (END) ====================
      },

      i = {
        -- type template string
        ["<C-CR>"] = { "<++>", desc = "Insert template string" },
        ["<S-Tab>"] = { "<C-V><Tab>", desc = "Tab character" },
        -- date/time input
        ["<c-t>"] = { desc = "󰃰 Date/Time" },
        ["<c-t>n"] = { "<c-r>=strftime('%Y-%m-%d')<cr>", desc = "Y-m-d" },
        ["<c-t>x"] = { "<c-r>=strftime('%m/%d/%y')<cr>", desc = "m/d/y" },
        ["<c-t>f"] = { "<c-r>=strftime('%B %d, %Y')<cr>", desc = "B d, Y" },
        ["<c-t>X"] = { "<c-r>=strftime('%H:%M')<cr>", desc = "H:M" },
        ["<c-t>F"] = { "<c-r>=strftime('%H:%M:%S')<cr>", desc = "H:M:S" },
        ["<c-t>d"] = { "<c-r>=strftime('%Y-%m-%d %H:%M:%S')<cr>", desc = "Y-m-d H:M:S" },

        -- ToggleTerm
        -- ==================== I: MY MAPPINGs (START) ======================
        ["<A-h>"] = {
          function() require("tmux").move_left() end,
          desc = "Navigate left",
        },
        ["<A-l>"] = {
          function() require("tmux").move_right() end,
          desc = "Navigate right",
        },
        ["<A-j>"] = {
          function() require("tmux").move_bottom() end,
          desc = "Navigate bottom",
        },
        ["<A-k>"] = {
          function() require("tmux").move_top() end,
          desc = "Navigate up",
        },
        ["<c-t><c-t>"] = { "<c-r>=strftime('%Y-%m-%d %H:%M:%S')<cr>", desc = "󰃰 Y-m-d H:M:S" },

        -- Neovide fullscreen
        ["<C-F11>"] = {
          function() vim.g.neovide_fullscreen = not vim.g.neovide_fullscreen end,
          desc = "Toggle Fullscreen",
          noremap = true,
          silent = true,
        },

        -- ==================== I: MY MAPPINGs (END) ======================
      },

      v = {
        -- ["<Leader>r"] = { "<Plug>Send", desc = "Send to REPL" },
        -- ["<Leader>r"] = {
        --   function()
        --     local a_orig = vim.fn.getreg "a"
        --     local mode = vim.fn.mode()
        --     if mode ~= "v" and mode ~= "V" then vim.cmd [[normal! gv]] end
        --     vim.cmd [[silent! normal! "aygv]]
        --     local text = vim.fn.getreg "a"
        --     vim.fn.setreg("a", a_orig)
        --     text = text:gsub("[\n\r]", ";")
        --     text = text:gsub(";;", "")
        --     -- vim.notify(text)
        --     vim.cmd("lua " .. text)
        --   end,
        --   desc = "Run via Lua",
        -- },

        -- Disable default Ctrl-Y/Ctrl-E scroll (same as normal mode)
        ["<C-y>"] = false,
        ["<C-e>"] = false,

        -- ==================== V: MY MAPPINGs (START) ====================
        -- ["<Leader>n"] = { desc = " Notes" },
        -- ["<Leader>a"] = { desc = " Edit" },

        -- send the ctrl-u + z. for centering
        -- ["u"] = { 'vscode-neovim.send "<C-u>z."', noremap = true, desc = "scroll up", silent = true },

        -- ["t"] = { "<cmd>lua require'hop'.hint_char2()<cr>", noremap = true, desc = "Hop", silent = true },
        ["<Leader><cr>"] = { "<cmd>WikiJournal<cr>", desc = "Journal" },
        ["<Leader><tab>"] = { "<cmd>WikiIndex<cr>", desc = "Todo" },
        ["<Leader>`"] = { "<cmd>WikiPages<cr>", desc = "Wiki Pages" },

        -- ["<Leader><cr>"] = { "<cmd>Neorg journal today<cr>", desc = "Journal" },
        -- ["<Leader><tab>"] = { "<cmd>Neorg index<cr>", desc = "Todo" },

        -- [","] = { "<cmd>VimwikiToggleListItem<cr>", desc = "Toggle Todo" },
        -- ["<"] = { "<cmd>TaskWikiToggle<cr><cr>", desc = "Start a Todo" },

        -- ["<Leader>np"] = { ":WikiJournalPrev<cr>", desc = "Diary (Prev Day)" },
        -- ["<Leader>nn"] = { ":WikiJournalNext<cr>", desc = "Diary (Next Day)" },

        ["<Leader>de"] = {
          function() require("dapui").eval() end,
          desc = "Evaluate Line",
        },

        -- Neovide fullscreen
        ["<C-F11>"] = {
          function() vim.g.neovide_fullscreen = not vim.g.neovide_fullscreen end,
          desc = "Toggle Fullscreen",
          noremap = true,
          silent = true,
        },

        -- ToggleTerm
        ["<Leader>s"] = {
          function()
            local trim_spaces = false
            require("toggleterm").send_lines_to_terminal("visual_lines", trim_spaces, { args = vim.v.count })
            -- send ENTER key
            -- require("toggleterm").exec("\n", 1)
          end,
          desc = " Run Line at Term",
        },
        -- ==================== V: MY MAPPINGs (END) ======================
      },

      t = {
        -- setting a mapping to false will disable it
        -- ["<esc>"] = false,
        ["<C-y>"] = { "<C-\\><C-n>", desc = "Terminal normal mode" },
        ["<esc><esc>"] = { "<C-\\><C-n>:q<cr>", desc = "Terminal quit" },

        -- Paste from clipboard
        ["<C-]>"] = { '<C-\\><C-n>"+pi', desc = "Paste from clipboard" },

        -- Tmux move pane
        ["<A-h>"] = {
          function() require("tmux").move_left() end,
          desc = "Tmux navigate left",
        },
        ["<A-l>"] = {
          function() require("tmux").move_right() end,
          desc = "Tmux navigate right",
        },
        ["<A-j>"] = {
          function() require("tmux").move_bottom() end,
          desc = "Tmux navigate bottom",
        },
        ["<A-k>"] = {
          function() require("tmux").move_top() end,
          desc = "Tmux navigate up",
        },
        ["<A-S-h>"] = {
          function() require("tmux").resize_left() end,
          desc = "Tmux resize left",
        },
        ["<A-S-l>"] = {
          function() require("tmux").resize_right() end,
          desc = "Tmux resize right",
        },
        ["<A-S-j>"] = {
          function() require("tmux").resize_bottom() end,
          desc = "Tmux resize bottom",
        },
        ["<A-S-k>"] = {
          function() require("tmux").resize_top() end,
          desc = "Tmux resize up",
        },

        -- Neovide fullscreen
        ["<C-F11>"] = {
          function() vim.g.neovide_fullscreen = not vim.g.neovide_fullscreen end,
          desc = "Toggle Fullscreen",
          noremap = true,
          silent = true,
        },
      },

      x = {
        -- better increment/decrement
        ["+"] = { "g<C-a>", desc = "Increment number" },
        ["-"] = { "g<C-x>", desc = "Descrement number" },
        -- line text-objects
        ["il"] = { "g_o^", desc = "Inside line text object" },
        ["al"] = { "$o^", desc = "Around line text object" },
        -- Easy-Align
        ga = { "<Plug>(EasyAlign)", desc = "Easy Align" },
      },

      o = {
        -- line text-objects
        ["il"] = { ":normal vil<cr>", desc = "Inside line text object" },
        ["al"] = { ":normal val<cr>", desc = "Around line text object" },
      },
    },

    autocmds = {
      -- autocommands are organized into augroups for easy management
      autohidetabline = {
        -- each augroup contains a list of auto commands
        {
          -- create a new autocmd on the "User" event
          event = "User",
          -- the pattern is the name of our User autocommand events
          pattern = "AstroBufsUpdated", -- triggered when vim.t.bufs is updated
          -- nice description
          desc = "Hide tabline when only one buffer and one tab",
          -- add the autocmd to the newly created augroup
          group = "autohidetabline",
          callback = function()
            -- if there is more than one buffer in the tab, show the tabline
            -- if there are 0 or 1 buffers in the tab, only show the tabline if there is more than one vim tab
            local new_showtabline = #vim.t.bufs > 1 and 2 or 1
            -- check if the new value is the same as the current value
            if new_showtabline ~= vim.opt.showtabline:get() then
              -- if it is different, then set the new `showtabline` value
              vim.opt.showtabline = new_showtabline
            end
          end,
        },
      },

      -- ==================== My Settings (START) ============================= --
      -- set_pyright_python_path = {
      --   {
      --     event = "BufEnter",
      --     pattern = "*.py",
      --     desc = "Set Pyright Python Path",
      --     callback = function()
      --       if not pyright_python_path_already_set then
      --         vim.defer_fn(function()
      --           vim.cmd "PyrightSetPythonPath /opt/conda/envs/paper/bin/python"
      --           pyright_python_path_already_set = true
      --         end, 3000)               -- 1000 milliseconds = 1 seconds
      --       end
      --     end,
      --   },
      -- },

      make_q_close_dap_floating_window = {
        -- each augroup contains a list of auto commands
        {
          -- create a new autocmd on the "User" event
          event = "User",
          pattern = "dap-float",
          desc = "Make q close dap floating debug window",
          group = "dapui",
          callback = function() vim.keymap.set("n", "q", "<cmd>close!<cr>") end,
        },
      },
    },
  },
}
