import React from 'react';
import ReactMarkdown from 'react-markdown';

const mdStyles = {
  root: { lineHeight: '1.8', fontSize: '14px', color: '#2d3436' },
};

export default function MarkdownText({ children, style }) {
  if (!children) return null;
  return (
    <div style={{ ...mdStyles.root, ...style }}>
      <ReactMarkdown>{children}</ReactMarkdown>
    </div>
  );
}
