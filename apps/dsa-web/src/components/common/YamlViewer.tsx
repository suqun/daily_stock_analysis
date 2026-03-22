import React, { useEffect, useState } from 'react';

interface YamlViewerProps {
  url: string;
  maxHeight?: string;
  className?: string;
}

/**
 * YAML 文件展示组件
 * 支持语法高亮和复制
 */
export const YamlViewer: React.FC<YamlViewerProps> = ({
  url,
  maxHeight = '500px',
  className = '',
}) => {
  const [content, setContent] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    const fetchYaml = async () => {
      try {
        const response = await fetch(url);
        if (!response.ok) {
          throw new Error(`加载失败: ${response.status}`);
        }
        const text = await response.text();
        setContent(text);
      } catch (err) {
        setError(err instanceof Error ? err.message : '加载失败');
      } finally {
        setLoading(false);
      }
    };
    void fetchYaml();
  }, [url]);

  const handleCopy = async () => {
    if (!content) return;
    await navigator.clipboard.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // YAML 语法高亮
  const highlightYaml = (yaml: string): React.ReactNode => {
    return yaml.split('\n').map((line, index) => {
      let highlighted = line;

      // 注释高亮 (以 # 开头)
      if (line.trim().startsWith('#')) {
        highlighted = `<span class="text-gray-500">${escapeHtml(line)}</span>`;
      } else {
        // key 高亮 (冒号前的部分)
        highlighted = line.replace(
          /^(\s*)([^:#\n]+)(:)/,
          '$1<span class="text-cyan-400">$2</span>$3'
        );
        // 字符串值高亮
        highlighted = highlighted.replace(
          /: ('.*?'|".*?")(\s*#.*)?$/,
          `: <span class="text-emerald-400">$1</span>${line.match(/\s+#.*$/)?.[0] ? `<span class="text-gray-500">${line.match(/\s+(#.*)$/)?.[1] || ''}</span>` : ''}`
        );
        // 数字值高亮
        highlighted = highlighted.replace(
          /: (-?\d+\.?\d*%?)(?=\s*$|\s*#)/,
          ': <span class="text-amber-400">$1</span>'
        );
        // 布尔值高亮
        highlighted = highlighted.replace(
          /: (true|false|null|yes|no)(?=\s*$|\s*#)/i,
          ': <span class="text-purple-400">$1</span>'
        );
        // 行内注释
        if (highlighted.includes('#') && !highlighted.includes('<span')) {
          highlighted = highlighted.replace(
            /(\s*[^#\n]+)(#.*)/,
            '$1<span class="text-gray-500">$2</span>'
          );
        }
      }

      return (
        <div
          key={index}
          className="leading-relaxed"
          dangerouslySetInnerHTML={{ __html: highlighted }}
        />
      );
    });
  };

  const escapeHtml = (str: string): string => {
    return str
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="text-sm text-gray-500">加载配置中...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-red-500 text-sm py-4 text-center">
        {error}
      </div>
    );
  }

  return (
    <div className={`relative ${className}`}>
      {/* 复制按钮 */}
      <button
        onClick={handleCopy}
        className="absolute top-2 right-2 px-2 py-1 text-xs rounded
          bg-slate-700 hover:bg-slate-600 text-gray-300
          transition-colors z-10"
      >
        {copied ? '已复制!' : '复制'}
      </button>

      {/* YAML 内容 */}
      <div
        className="bg-slate-900/80 rounded-lg p-4 overflow-auto custom-scrollbar
          border border-slate-700/50 font-mono text-sm text-gray-300"
        style={{ maxHeight }}
      >
        <pre className="whitespace-pre-wrap break-words">
          {highlightYaml(content || '')}
        </pre>
      </div>
    </div>
  );
};
