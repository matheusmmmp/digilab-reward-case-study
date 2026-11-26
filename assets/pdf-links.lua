-- PDF reports (format: typst): a relative link to another page of the site (an .ipynb, .qmd or .md
-- source, possibly with an #anchor) cannot work in a downloaded PDF, so it is rewritten to the
-- published page on the site. Links within the same document (#anchor) and absolute URLs are kept.

local SITE = "https://matheusmmmp.github.io/digilab-reward-case-study/"

local function normalize(path)
  local parts = {}
  for seg in path:gmatch("[^/]+") do
    if seg == ".." then
      table.remove(parts)
    elseif seg ~= "." then
      table.insert(parts, seg)
    end
  end
  return table.concat(parts, "/")
end

local function doc_dir()
  local input = quarto.doc.input_file:gsub("\\", "/")
  local root = quarto.project.directory:gsub("\\", "/")
  local rel = input:sub(#root + 2)
  return rel:match("^(.*)/[^/]*$") or ""
end

function Link(el)
  local target = el.target
  if target:match("^%a[%w+.-]*:") or target:match("^#") or target == "" then
    return nil
  end
  local path, anchor = target:match("^([^#]*)(#?.*)$")
  local page = path:gsub("%.ipynb$", ".html"):gsub("%.qmd$", ".html"):gsub("%.md$", ".html")
  if page == "index.html" or page:match("/index%.html$") then
    page = page:gsub("index%.html$", "")
  end
  local dir = doc_dir()
  local full = normalize((dir ~= "" and (dir .. "/") or "") .. page)
  el.target = SITE .. full .. anchor
  return el
end
