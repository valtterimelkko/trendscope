'use client'

import { useEditor, EditorContent } from '@tiptap/react'
import StarterKit from '@tiptap/starter-kit'
import Image from '@tiptap/extension-image'
import Link from '@tiptap/extension-link'
import Placeholder from '@tiptap/extension-placeholder'

interface RichTextEditorProps {
  content: string
  onChange: (content: string) => void
  placeholder?: string
}

export function RichTextEditor({ content, onChange, placeholder = 'Start writing...' }: RichTextEditorProps) {
  const editor = useEditor({
    extensions: [
      StarterKit.configure({
        heading: {
          levels: [1, 2, 3],
        },
      }),
      Image.configure({
        allowBase64: true,
        HTMLAttributes: {
          class: 'rounded-lg max-w-full',
        },
      }),
      Link.configure({
        openOnClick: false,
        HTMLAttributes: {
          class: 'text-primary underline',
        },
      }),
      Placeholder.configure({
        placeholder,
      }),
    ],
    content,
    onUpdate: ({ editor }) => {
      onChange(editor.getHTML())
    },
    editorProps: {
      attributes: {
        class: 'editor-content prose prose-lg max-w-none focus:outline-none',
      },
    },
  })

  if (!editor) return null

  return (
    <div className="editor-container">
      {/* Toolbar */}
      <div className="editor-toolbar">
        <button
          onClick={() => editor.chain().focus().toggleBold().run()}
          className={`editor-toolbar-btn ${editor.isActive('bold') ? 'is-active' : ''}`}
          title="Bold"
        >
          <BoldIcon className="w-4 h-4" />
        </button>
        <button
          onClick={() => editor.chain().focus().toggleItalic().run()}
          className={`editor-toolbar-btn ${editor.isActive('italic') ? 'is-active' : ''}`}
          title="Italic"
        >
          <ItalicIcon className="w-4 h-4" />
        </button>
        <button
          onClick={() => editor.chain().focus().toggleStrike().run()}
          className={`editor-toolbar-btn ${editor.isActive('strike') ? 'is-active' : ''}`}
          title="Strikethrough"
        >
          <StrikeIcon className="w-4 h-4" />
        </button>

        <div className="w-px h-5 bg-border mx-1" />

        <button
          onClick={() => editor.chain().focus().toggleHeading({ level: 1 }).run()}
          className={`editor-toolbar-btn ${editor.isActive('heading', { level: 1 }) ? 'is-active' : ''}`}
          title="Heading 1"
        >
          <span className="text-xs font-bold">H1</span>
        </button>
        <button
          onClick={() => editor.chain().focus().toggleHeading({ level: 2 }).run()}
          className={`editor-toolbar-btn ${editor.isActive('heading', { level: 2 }) ? 'is-active' : ''}`}
          title="Heading 2"
        >
          <span className="text-xs font-bold">H2</span>
        </button>
        <button
          onClick={() => editor.chain().focus().toggleHeading({ level: 3 }).run()}
          className={`editor-toolbar-btn ${editor.isActive('heading', { level: 3 }) ? 'is-active' : ''}`}
          title="Heading 3"
        >
          <span className="text-xs font-bold">H3</span>
        </button>

        <div className="w-px h-5 bg-border mx-1" />

        <button
          onClick={() => editor.chain().focus().toggleBulletList().run()}
          className={`editor-toolbar-btn ${editor.isActive('bulletList') ? 'is-active' : ''}`}
          title="Bullet List"
        >
          <ListIcon className="w-4 h-4" />
        </button>
        <button
          onClick={() => editor.chain().focus().toggleOrderedList().run()}
          className={`editor-toolbar-btn ${editor.isActive('orderedList') ? 'is-active' : ''}`}
          title="Numbered List"
        >
          <OrderedListIcon className="w-4 h-4" />
        </button>
        <button
          onClick={() => editor.chain().focus().toggleBlockquote().run()}
          className={`editor-toolbar-btn ${editor.isActive('blockquote') ? 'is-active' : ''}`}
          title="Quote"
        >
          <QuoteIcon className="w-4 h-4" />
        </button>

        <div className="w-px h-5 bg-border mx-1" />

        <button
          onClick={() => {
            const url = window.prompt('Enter image URL')
            if (url) {
              editor.chain().focus().setImage({ src: url }).run()
            }
          }}
          className="editor-toolbar-btn"
          title="Insert Image"
        >
          <ImageIcon className="w-4 h-4" />
        </button>
        <button
          onClick={() => {
            const url = window.prompt('Enter link URL')
            if (url) {
              editor.chain().focus().setLink({ href: url }).run()
            }
          }}
          className={`editor-toolbar-btn ${editor.isActive('link') ? 'is-active' : ''}`}
          title="Insert Link"
        >
          <LinkIcon className="w-4 h-4" />
        </button>
      </div>

      {/* Editor content */}
      <EditorContent editor={editor} />
    </div>
  )
}

// Icons
function BoldIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M6 4h8a4 4 0 014 4 4 4 0 01-4 4H6V4zm0 8h9a4 4 0 014 4 4 4 0 01-4 4H6v-8z" />
    </svg>
  )
}

function ItalicIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 4h4m-2 0v16m-4 0h4" transform="skewX(-10)" />
    </svg>
  )
}

function StrikeIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 12h16M12 4c-2.5 0-4 1.5-4 3.5S9.5 11 12 11s4-1 4-3.5S14.5 4 12 4zm0 16c2.5 0 4-1.5 4-3.5S14.5 13 12 13s-4 1-4 3.5S9.5 20 12 20z" />
    </svg>
  )
}

function ListIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
    </svg>
  )
}

function OrderedListIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 6h11M9 12h11M9 18h11M4 6v2m0 4v2m0 4v2" />
    </svg>
  )
}

function QuoteIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
    </svg>
  )
}

function ImageIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
    </svg>
  )
}

function LinkIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
    </svg>
  )
}
