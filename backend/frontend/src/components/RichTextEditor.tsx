import { useEffect, useRef, useState, type ReactNode } from "react";
import { AlignCenter, AlignJustify, AlignLeft, AlignRight, Bold, Italic, Link, List, Underline } from "lucide-react";
import { safeUrl } from "../shared/resumeFormat";
import { sanitizeRichText, toEditorHTML } from "./RichTextContent";
export { RichTextContent, sanitizeRichText } from "./RichTextContent";

type Command = "bold" | "italic" | "underline" | "insertUnorderedList" | "createLink" | "justifyLeft" | "justifyCenter" | "justifyRight" | "justifyFull";


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
