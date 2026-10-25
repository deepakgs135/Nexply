import { useEffect, useRef, useState, type ReactNode } from "react";
import { AlignCenter, AlignJustify, AlignLeft, AlignRight, Bold, Italic, Link, List, Underline } from "lucide-react";
import { safeUrl } from "../shared/resumeFormat";

type Command = "bold" | "italic" | "underline" | "insertUnorderedList" | "createLink" | "justifyLeft" | "justifyCenter" | "justifyRight" | "justifyFull";

function escapeHtml(value: string) {
  return value.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/\"/g, "&quot;");
}

export function sanitizeRichText(html: string): string {
  if (typeof DOMParser === "undefined") return html.replace(/<[^>]*>/g, "");
  const parsed = new DOMParser().parseFromString(html, "text/html");
  const serialize = (node: Node): string => {
    if (node.nodeType === Node.TEXT_NODE) return escapeHtml(node.textContent || "");
    if (!(node instanceof HTMLElement)) return "";
    const children = Array.from(node.childNodes).map(serialize).join("");
    const tag = node.tagName.toLowerCase();
    if (tag === "br") return "<br>";
    if (["b", "strong"].includes(tag)) return `<strong>${children}</strong>`;
    if (["i", "em"].includes(tag)) return `<em>${children}</em>`;
    if (tag === "u") return `<u>${children}</u>`;
    if (tag === "ul" || tag === "ol" || tag === "li") return `<${tag}>${children}</${tag}>`;
    if (tag === "a") {
      const href = safeUrl(node.getAttribute("href") || "");
      return href ? `<a href="${escapeHtml(href)}">${children}</a>` : children;
    }
    if (tag === "p" || tag === "div") {
      const alignment = ["left", "center", "right", "justify"].includes(node.style.textAlign) ? node.style.textAlign : "";
      return `<p${alignment ? ` style="text-align:${alignment}"` : ""}>${children}</p>`;
    }
    return children;
  };
  return Array.from(parsed.body.childNodes).map(serialize).join("");
}

function toEditorHTML(value: string) {
  if (/<\/?(p|div|br|strong|b|em|i|u|ul|ol|li|a)\b/i.test(value)) return sanitizeRichText(value);
  return escapeHtml(value).replace(/\r?\n/g, "<br>");
}

export function RichTextContent({ value }: { value: string }): ReactNode {
  if (typeof DOMParser === "undefined") return value;
  const parsed = new DOMParser().parseFromString(toEditorHTML(value), "text/html");
  const render = (node: Node, key: string): ReactNode => {
    if (node.nodeType === Node.TEXT_NODE) return node.textContent;
    if (!(node instanceof HTMLElement)) return null;
    const tag = node.tagName.toLowerCase();
    const children = Array.from(node.childNodes).map((child, index) => render(child, `${key}-${index}`));
    if (tag === "br") return <br key={key} />;
    if (tag === "strong" || tag === "b") return <strong key={key}>{children}</strong>;
    if (tag === "em" || tag === "i") return <em key={key}>{children}</em>;
    if (tag === "u") return <u key={key}>{children}</u>;
    if (tag === "ul") return <ul key={key}>{children}</ul>;
    if (tag === "ol") return <ol key={key}>{children}</ol>;
    if (tag === "li") return <li key={key}>{children}</li>;
    if (tag === "a") {
      const href = safeUrl(node.getAttribute("href") || "");
      return href ? <a key={key} href={href} target="_blank" rel="noreferrer">{children}</a> : <span key={key}>{children}</span>;
    }
    if (tag === "p" || tag === "div") {
      const alignment = ["left", "center", "right", "justify"].includes(node.style.textAlign) ? node.style.textAlign as "left" | "center" | "right" | "justify" : undefined;
      return <p key={key} style={{ textAlign: alignment }}>{children}</p>;
    }
    return <span key={key}>{children}</span>;
  };
  return <>{Array.from(parsed.body.childNodes).map((node, index) => render(node, `rich-${index}`))}</>;
}

export default function RichTextEditor({ value, onChange, placeholder, label }: { value: string; onChange: (value: string) => void; placeholder: string; label: string }) {
  const editorRef = useRef<HTMLDivElement>(null);
  const [activeCommands, setActiveCommands] = useState<Set<Command>>(new Set());
  useEffect(() => {
    const editor = editorRef.current;
    if (editor && document.activeElement !== editor) editor.innerHTML = toEditorHTML(value);
  }, [value]);

  function updateActiveCommands() {
    const editor = editorRef.current;
    const selection = window.getSelection();
    if (!editor || !selection?.anchorNode || !editor.contains(selection.anchorNode)) return;
    const commands: Command[] = ["bold", "italic", "underline", "insertUnorderedList", "createLink", "justifyLeft", "justifyCenter", "justifyRight", "justifyFull"];
    setActiveCommands(new Set(commands.filter((command) => document.queryCommandState(command))));
  }

  function runCommand(command: Command) {
    editorRef.current?.focus();
    document.execCommand(command, false);
    if (editorRef.current) onChange(sanitizeRichText(editorRef.current.innerHTML));
    updateActiveCommands();
  }
  function addLink() {
    const entered = window.prompt("Paste a link (https://…)");
    if (!entered) return;
    const href = safeUrl(entered.trim());
    if (!href) return;
    editorRef.current?.focus();
    document.execCommand("createLink", false, href);
    if (editorRef.current) onChange(sanitizeRichText(editorRef.current.innerHTML));
    updateActiveCommands();
  }
  const tools: Array<{ label: string; icon: ReactNode; command: Command }> = [
    { label: "Bold", icon: <Bold size={18} />, command: "bold" },
    { label: "Italic", icon: <Italic size={18} />, command: "italic" },
    { label: "Underline", icon: <Underline size={18} />, command: "underline" },
    { label: "Bulleted list", icon: <List size={19} />, command: "insertUnorderedList" },
  ];
  const alignTools: Array<{ label: string; icon: ReactNode; command: Command }> = [
    { label: "Align left", icon: <AlignLeft size={18} />, command: "justifyLeft" },
    { label: "Align center", icon: <AlignCenter size={18} />, command: "justifyCenter" },
    { label: "Align right", icon: <AlignRight size={18} />, command: "justifyRight" },
    { label: "Justify text", icon: <AlignJustify size={18} />, command: "justifyFull" },
  ];
  return <div className="rich-text-editor">
    <div className="rich-text-toolbar" role="toolbar" aria-label={`${label} formatting`}>
      {tools.map((tool) => <span className="rich-toolbar-item" key={tool.command}><button className={activeCommands.has(tool.command) ? "is-active" : ""} type="button" title={tool.label} aria-label={tool.label} aria-pressed={activeCommands.has(tool.command)} onMouseDown={(event) => event.preventDefault()} onClick={() => runCommand(tool.command)}>{tool.icon}</button></span>)}
      <span className="rich-toolbar-item toolbar-divider-before"><button className={activeCommands.has("createLink") ? "is-active" : ""} type="button" title="Insert link" aria-label="Insert link" aria-pressed={activeCommands.has("createLink")} onMouseDown={(event) => event.preventDefault()} onClick={addLink}><Link size={19} /></button></span>
      {alignTools.map((tool, index) => <span className={`rich-toolbar-item ${index === 0 ? "toolbar-divider-before" : ""}`} key={tool.command}><button className={activeCommands.has(tool.command) ? "is-active" : ""} type="button" title={tool.label} aria-label={tool.label} aria-pressed={activeCommands.has(tool.command)} onMouseDown={(event) => event.preventDefault()} onClick={() => runCommand(tool.command)}>{tool.icon}</button></span>)}
    </div>
    <div ref={editorRef} className="rich-text-canvas" contentEditable suppressContentEditableWarning role="textbox" aria-label={label} aria-multiline="true" data-placeholder={placeholder} onFocus={updateActiveCommands} onKeyUp={updateActiveCommands} onMouseUp={updateActiveCommands} onInput={(event) => { onChange(sanitizeRichText(event.currentTarget.innerHTML)); updateActiveCommands(); }} onBlur={(event) => { const clean = sanitizeRichText(event.currentTarget.innerHTML); event.currentTarget.innerHTML = toEditorHTML(clean); onChange(clean); }} onPaste={(event) => { event.preventDefault(); const text = event.clipboardData.getData("text/plain"); document.execCommand("insertText", false, text); updateActiveCommands(); }} />
  </div>;
}
