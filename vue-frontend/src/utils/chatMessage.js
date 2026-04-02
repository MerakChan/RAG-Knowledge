export const formatMessageTime = (value) => {
  if (!value) return ''
  const match = String(value).match(/(\d{2}:\d{2})(?::\d{2})?$/)
  return match ? match[1] : String(value)
}

const splitPipeRow = (line) => line
  .trim()
  .replace(/^\|/, '')
  .replace(/\|$/, '')
  .split('|')
  .map((cell) => cell.trim())

const extractMarkdownTable = (text) => {
  const lines = String(text || '').split('\n')
  for (let index = 0; index < lines.length - 1; index += 1) {
    const headerLine = lines[index]
    const separatorLine = lines[index + 1]
    const isHeader = /^\s*\|.*\|\s*$/.test(headerLine)
    const isSeparator = /^\s*\|(?:\s*:?-{3,}:?\s*\|)+\s*$/.test(separatorLine)

    if (!isHeader || !isSeparator) continue

    const rows = []
    let cursor = index + 2
    while (cursor < lines.length && /^\s*\|.*\|\s*$/.test(lines[cursor])) {
      rows.push(splitPipeRow(lines[cursor]))
      cursor += 1
    }

    const cleanText = [...lines.slice(0, index), ...lines.slice(cursor)].join('\n').trim()
    return {
      cleanText,
      table: {
        headers: splitPipeRow(headerLine),
        rows
      }
    }
  }

  return {
    cleanText: String(text || '').trim(),
    table: null
  }
}

const normalizeSectionText = (text) => String(text || '')
  .replace(/\r\n/g, '\n')
  .replace(/\r/g, '\n')
  .trim()

const THINK_PATTERN = /\[(?:思考|鎬濊€僜|闁诡剚绻嗛埀顒€鍎?)\]\s*[：:]\s*([\s\S]*?)(?=\n\s*\[(?:回答|鍥炵瓟|闁搞儳鍋熼悺?)\]\s*[：:]|$)/
const ANSWER_PATTERN = /\[(?:回答|鍥炵瓟|闁搞儳鍋熼悺?)\]\s*[：:]\s*([\s\S]*)$/

const splitSections = (text) => {
  const raw = normalizeSectionText(text)
  if (!raw) return { thought: '', answer: raw }

  const thinkTagMatch = raw.match(/<think>([\s\S]*?)<\/think>/i)
  if (thinkTagMatch) {
    return {
      thought: normalizeSectionText(thinkTagMatch[1]),
      answer: normalizeSectionText(raw.replace(thinkTagMatch[0], ''))
    }
  }

  const thoughtMatch = raw.match(THINK_PATTERN)
  const answerMatch = raw.match(ANSWER_PATTERN)
  const thought = thoughtMatch ? normalizeSectionText(thoughtMatch[1]) : ''
  let answer = answerMatch ? normalizeSectionText(answerMatch[1]) : raw

  if (thought && !answerMatch && thoughtMatch) {
    answer = normalizeSectionText(raw.replace(thoughtMatch[0], ''))
  }

  return { thought, answer }
}

const cleanupAnswerText = (text) => normalizeSectionText(text)
  .replace(/^已根据数据源完成查询。?/m, '')
  .replace(/^已根据数据源完成查询，SQL 如下：?/m, '')
  .replace(/^查询结果如下：?/m, '')
  .trim()

export const parseAssistantContent = (content) => {
  const raw = normalizeSectionText(content)
  if (!raw) {
    return { thought: '', answer: '', sqlQuery: '', table: null }
  }

  let { thought, answer } = splitSections(raw)

  const nested = splitSections(answer)
  if (nested.thought || nested.answer !== answer) {
    thought = [thought, nested.thought].filter(Boolean).join('\n\n').trim()
    answer = nested.answer
  }

  const sqlBlockMatch = answer.match(/```sql\s*([\s\S]*?)```/i) || raw.match(/```sql\s*([\s\S]*?)```/i)
  const inlineSqlMatch = answer.match(/SQL\s*[：:]\s*`([^`]+)`/i) || raw.match(/SQL\s*[：:]\s*`([^`]+)`/i)
  const sqlQuery = normalizeSectionText(sqlBlockMatch?.[1] || inlineSqlMatch?.[1] || '')

  if (sqlBlockMatch?.[0] && answer.includes(sqlBlockMatch[0])) {
    answer = answer.replace(sqlBlockMatch[0], '').trim()
  }

  const { cleanText, table } = extractMarkdownTable(answer)
  answer = cleanupAnswerText(cleanText)

  return {
    thought,
    answer,
    sqlQuery,
    table
  }
}
