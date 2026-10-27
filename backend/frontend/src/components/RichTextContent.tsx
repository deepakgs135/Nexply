import type { ReactNode } from "react";
import { safeUrl } from "../shared/resumeFormat";

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

export function toEditorHTML(value: string) {
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

