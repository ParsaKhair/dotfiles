local ls = require("luasnip")
local s = ls.snippet
local sn = ls.snippet_node
local t = ls.text_node
local i = ls.insert_node
local f = ls.function_node
local fmta = require("luasnip.extras.fmt").fmta

local tex_utils = {}
tex_utils.in_mathzone = function()
  return vim.fn["vimtex#syntax#in_mathzone"]() == 1
end

local function math_cond(_, _)
  return tex_utils.in_mathzone()
end

return {

  -- ===== QUANTUM MECHANICS =====

  s(
    { trig = "bra", snippetType = "autosnippet" },
    fmta([[\langle <> |]], { i(1, "\\psi") }),
    { condition = math_cond }
  ),

  s(
    { trig = "ket", snippetType = "autosnippet" },
    fmta([[| <> \rangle]], { i(1, "\\psi") }),
    { condition = math_cond }
  ),

  s(
    { trig = "brk", snippetType = "autosnippet" },
    fmta([[\langle <> \lvert <> \rangle]], { i(1, "\\psi"), i(2, "\\phi") }),
    { condition = math_cond }
  ),

  s(
    { trig = "braopket", snippetType = "autosnippet" },
    fmta([[\langle <> \lvert <> \rvert <> \rangle]], { i(1, "\\psi"), i(2, "\\hat{A}"), i(3, "\\phi") }),
    { condition = math_cond }
  ),

  s(
    { trig = "expec", snippetType = "autosnippet" },
    fmta([[\langle <> \rangle]], { i(1, "\\hat{A}") }),
    { condition = math_cond }
  ),

  s(
    { trig = "comm", snippetType = "autosnippet" },
    fmta("[<>, <>]", { i(1, "\\hat{A}"), i(2, "\\hat{B}") }),
    { condition = math_cond }
  ),

  s({ trig = "hbar", snippetType = "autosnippet" }, t("\\hbar"), { condition = math_cond }),

  s(
    { trig = "sch", snippetType = "autosnippet" },
    t([[i\hbar \frac{\partial}{\partial t} \Psi = \hat{H}\Psi]]),
    { condition = math_cond }
  ),

  s({ trig = "tise", snippetType = "autosnippet" }, t([[\hat{H}\psi = E\psi]]), { condition = math_cond }),

  s({ trig = "ham", snippetType = "autosnippet" }, t([[\hat{H}]]), { condition = math_cond }),

  -- auto-hat: type a letter then "hat" -> \hat{letter}
  s(
    { trig = "([A-Za-z])hat", regTrig = true, snippetType = "autosnippet" },
    f(function(_, snip)
      return "\\hat{" .. snip.captures[1] .. "}"
    end),
    { condition = math_cond }
  ),

  -- auto-dagger: letter + "dg" -> letter^\dagger
  s(
    { trig = "([A-Za-z])dg", regTrig = true, snippetType = "autosnippet" },
    f(function(_, snip)
      return snip.captures[1] .. "^\\dagger"
    end),
    { condition = math_cond }
  ),

  s({ trig = "del2", snippetType = "autosnippet" }, t([[\nabla^2]]), { condition = math_cond }),

  s(
    { trig = "eigen", snippetType = "autosnippet" },
    fmta([[\hat{<>}\lvert <> \rangle = <> \lvert <> \rangle]], { i(1, "A"), i(2, "a"), i(3, "a"), i(4, "a") }),
    { condition = math_cond }
  ),

  s(
    { trig = "updown", snippetType = "autosnippet" },
    t([[\lvert \uparrow \rangle, \lvert \downarrow \rangle]]),
    { condition = math_cond }
  ),

  s({ trig = "pauli", snippetType = "autosnippet" }, t([[\sigma_x, \sigma_y, \sigma_z]]), { condition = math_cond }),
  s(
    { trig = "pd", snippetType = "autosnippet" },
    fmta([[\frac{\partial <>}{\partial <>}]], {
      i(1, "F"),
      i(2, "s"),
    }),
    { condition = math_cond }
  ),

  -- ===== ELECTRODYNAMICS =====

  s(
    { trig = "div", snippetType = "autosnippet" },
    fmta([[\nabla \cdot \vec{<>}]], { i(1, "E") }),
    { condition = math_cond }
  ),

  s(
    { trig = "curl", snippetType = "autosnippet" },
    fmta([[\nabla \times \vec{<>}]], { i(1, "B") }),
    { condition = math_cond }
  ),

  s({ trig = "grad", snippetType = "autosnippet" }, fmta([[\nabla <>]], { i(1, "\\phi") }), { condition = math_cond }),

  s({ trig = "lap", snippetType = "autosnippet" }, fmta([[\nabla^2 <>]], { i(1, "\\phi") }), { condition = math_cond }),

  s("max1", t([[\nabla \cdot \vec{E} = \dfrac{\rho}{\epsilon_0}]])),

  s("max2", t([[\nabla \cdot \vec{B} = 0]])),

  s("max3", t([[\nabla \times \vec{E} = -\dfrac{\partial \vec{B}}{\partial t}]])),

  s("max4", t([[\nabla \times \vec{B} = \mu_0\vec{J} + \mu_0\epsilon_0 \dfrac{\partial \vec{E}}{\partial t}]])),

  s({ trig = "eps0", snippetType = "autosnippet" }, t([[\epsilon_0]]), { condition = math_cond }),

  s({ trig = "mu0", snippetType = "autosnippet" }, t([[\mu_0]]), { condition = math_cond }),

  -- auto-vec: letter + "vec" -> \vec{letter}
  s(
    { trig = "([A-Za-z])vec", regTrig = true, snippetType = "autosnippet" },
    f(function(_, snip)
      return "\\vec{" .. snip.captures[1] .. "}"
    end),
    { condition = math_cond }
  ),

  s(
    { trig = "dda", snippetType = "autosnippet" },
    fmta([[\dfrac{d\vec{<>}}{dt}]], { i(1, "A") }),
    { condition = math_cond }
  ),

  s(
    { trig = "int", snippetType = "autosnippet" },
    fmta([[\displaystyle\int_{<>}^{<>}]], { i(1, "a"), i(2, "b") }),
    { condition = math_cond }
  ),

  s({ trig = "oint", snippetType = "autosnippet" }, t([[\oint]]), { condition = math_cond }),

  s("poynt", t([[\vec{S} = \dfrac{1}{\mu_0}\vec{E}\times\vec{B}]])),

  s("lorentz", t([[\vec{F} = q(\vec{E} + \vec{v}\times\vec{B})]])),

  s("wave", t([[\nabla^2 \vec{E} - \mu_0\epsilon_0\dfrac{\partial^2 \vec{E}}{\partial t^2} = 0]])),
}
