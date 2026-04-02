const escapeHtml = (value = '') => String(value)
  .replace(/&/g, '&amp;')
  .replace(/</g, '&lt;')
  .replace(/>/g, '&gt;')
  .replace(/"/g, '&quot;')
  .replace(/'/g, '&#39;')

const renderInline = (value = '') => {
  let rendered = escapeHtml(value)
  rendered = rendered.replace(/`([^`]+)`/g, '<code>$1</code>')
  rendered = rendered.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
  rendered = rendered.replace(/\*([^*]+)\*/g, '<em>$1</em>')
  rendered = rendered.replace(/\[([^\]]+)\]\((https?:\/\/[^)]+)\)/g, '<a href="$2" target="_blank" rel="noreferrer">$1</a>')
  return rendered
}

const renderTable = (lines = []) => {
  if (lines.length < 2) return ''
  const [headerLine, , ...bodyLines] = lines
  const toCells = (line) => line
    .trim()
    .replace(/^\|/, '')
    .replace(/\|$/, '')
    .split('|')
    .map((cell) => cell.trim())

  const headers = toCells(headerLine)
  const rows = bodyLines.map(toCells)

  return `<div class="md-table-shell"><table><thead><tr>${headers.map((cell) => `<th>${renderInline(cell)}</th>`).join('')}</tr></thead><tbody>${rows.map((row) => `<tr>${row.map((cell) => `<td>${renderInline(cell)}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`
}

export const renderMarkdown = (markdown = '') => {
  const source = String(markdown || '').replace(/\r\n/g, '\n')
  if (!source.trim()) return ''

  const blocks = source.split(/\n{2,}/)
  return blocks.map((block) => {
    const trimmed = block.trim()

    if (/^\|.*\|\n\|(?:\s*:?-{3,}:?\s*\|)+/m.test(trimmed)) {
      return renderTable(trimmed.split('\n'))
    }

    if (/^>\s+/.test(trimmed)) {
      const quote = trimmed.split('\n').map((line) => line.replace(/^>\s?/, '')).join('<br />')
      return `<blockquote>${renderInline(quote)}</blockquote>`
    }

    if (/^```/.test(block.trim())) {
      const match = block.match(/^```([\w-]*)\n?([\s\S]*?)```$/)
      if (!match) {
        return `<pre><code>${escapeHtml(block)}</code></pre>`
      }
      return `<pre><code class="language-${escapeHtml(match[1] || 'text')}">${escapeHtml(match[2].trim())}</code></pre>`
    }

    const lines = block.split('\n')
    if (lines.every((line) => /^[-*]\s+/.test(line.trim()))) {
      return `<ul>${lines.map((line) => `<li>${renderInline(line.replace(/^[-*]\s+/, ''))}</li>`).join('')}</ul>`
    }

    if (lines.every((line) => /^\d+\.\s+/.test(line.trim()))) {
      return `<ol>${lines.map((line) => `<li>${renderInline(line.replace(/^\d+\.\s+/, ''))}</li>`).join('')}</ol>`
    }

    if (/^###\s+/.test(trimmed)) {
      return `<h3>${renderInline(trimmed.replace(/^###\s+/, ''))}</h3>`
    }
    if (/^##\s+/.test(trimmed)) {
      return `<h2>${renderInline(trimmed.replace(/^##\s+/, ''))}</h2>`
    }
    if (/^#\s+/.test(trimmed)) {
      return `<h1>${renderInline(trimmed.replace(/^#\s+/, ''))}</h1>`
    }

    return `<p>${lines.map((line) => renderInline(line)).join('<br />')}</p>`
  }).join('')
}
