import clsx from 'clsx'
import type { Components } from 'react-markdown'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { oneDark, oneLight } from 'react-syntax-highlighter/dist/esm/styles/prism'

export function messageMarkdownComponents(isHuman: boolean): Components {
  const isDarkMode = document.documentElement.classList.contains('dark')
  const textClassName = isHuman ? 'text-white' : 'text-gray-900'
  const mutedTextClassName = isHuman ? 'text-indigo-100' : 'text-gray-700'
  const linkClassName = isHuman
    ? 'text-white underline underline-offset-2'
    : 'text-indigo-700 underline underline-offset-2'
  const inlineCodeClassName = isHuman
    ? 'rounded bg-indigo-500/70 px-1 py-0.5 font-mono text-[0.9em] text-white'
    : 'rounded bg-gray-100 px-1 py-0.5 font-mono text-[0.9em] text-gray-900'

  return {
    p: ({ ...props }) => <p className={clsx('mb-3 leading-6 last:mb-0', textClassName)} {...props} />,
    ul: ({ ...props }) => (
      <ul className={clsx('mb-3 list-disc space-y-1 pl-5 last:mb-0', mutedTextClassName)} {...props} />
    ),
    ol: ({ ...props }) => (
      <ol className={clsx('mb-3 list-decimal space-y-1 pl-5 last:mb-0', mutedTextClassName)} {...props} />
    ),
    li: ({ ...props }) => <li className="leading-6" {...props} />,
    blockquote: ({ ...props }) => (
      <blockquote
        className={clsx(
          'mb-3 border-l-4 pl-4 italic last:mb-0',
          isHuman ? 'border-indigo-200 text-indigo-100' : 'border-gray-300 text-gray-600'
        )}
        {...props}
      />
    ),
    a: ({ ...props }) => (
      <a
        className={linkClassName}
        target="_blank"
        rel="noreferrer"
        {...props}
      />
    ),
    code({ children, className, ...props }) {
      const match = /language-(\w+)/.exec(className || '')
      const codeContent = String(children).replace(/\n$/, '')

      if (match) {
        return (
          <SyntaxHighlighter
            PreTag="div"
            language={match[1]}
            style={isDarkMode ? oneDark : oneLight}
            customStyle={{
              margin: '0 0 0.75rem 0',
              borderRadius: '0.75rem',
              fontSize: '0.85rem',
              padding: '1rem',
            }}
          >
            {codeContent}
          </SyntaxHighlighter>
        )
      }

      return (
        <code className={inlineCodeClassName} {...props}>
          {children}
        </code>
      )
    },
    pre: ({ ...props }) => <>{props.children}</>,
    strong: ({ ...props }) => <strong className={clsx('font-semibold', textClassName)} {...props} />,
  }
}
