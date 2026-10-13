import DOMPurify from 'dompurify'
import { marked } from 'marked'

marked.use({
  gfm: true,
  breaks: true,
  headerIds: false,
  mangle: false,
})

export function renderMarkdown(content) {
  const html = marked.parse(content ?? '')
  return DOMPurify.sanitize(html)
}