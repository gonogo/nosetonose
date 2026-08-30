import { marked } from 'marked';
import type { Article, EditorialPage } from './types';

marked.setOptions({ gfm: true, breaks: false });

export function renderMarkdown(source: string): string {
	if (!source.trim()) return '';
	return marked.parse(source, { async: false }) as string;
}

export function parseFrontMatter(raw: string): { data: Record<string, string>; body: string } {
	const match = raw.match(/^---\r?\n([\s\S]*?)\r?\n---\r?\n?([\s\S]*)$/);
	if (!match) return { data: {}, body: raw.trim() };

	const data: Record<string, string> = {};
	for (const line of match[1].split('\n')) {
		const idx = line.indexOf(':');
		if (idx === -1) continue;
		const key = line.slice(0, idx).trim();
		let value = line.slice(idx + 1).trim();
		if (
			(value.startsWith('"') && value.endsWith('"')) ||
			(value.startsWith("'") && value.endsWith("'"))
		) {
			value = value.slice(1, -1).replace(/\\"/g, '"');
		}
		data[key] = value;
	}
	return { data, body: match[2].trim() };
}

const pageFiles = import.meta.glob('./content/pages/*.md', {
	eager: true,
	query: '?raw',
	import: 'default'
}) as Record<string, string>;

const articleFiles = import.meta.glob('./content/articles/*.md', {
	eager: true,
	query: '?raw',
	import: 'default'
}) as Record<string, string>;

function fileSlug(path: string): string {
	return path.split('/').pop()?.replace(/\.md$/, '') ?? path;
}

export const editorialPages: EditorialPage[] = Object.entries(pageFiles).map(([path, raw]) => {
	const { data, body } = parseFrontMatter(raw);
	return {
		slug: fileSlug(path),
		title: data.title || fileSlug(path),
		body
	};
});

export const articles: Article[] = Object.entries(articleFiles)
	.map(([path, raw]) => {
		const { data, body } = parseFrontMatter(raw);
		const slug = fileSlug(path);
		return {
			slug,
			title: data.title || slug,
			source_url: data.source_url || null,
			body
		};
	})
	.sort((a, b) => a.title.localeCompare(b.title));

export function getEditorialPage(slug: string): EditorialPage | undefined {
	return editorialPages.find((page) => page.slug === slug);
}

export function getArticle(slug: string): Article | undefined {
	return articles.find((article) => article.slug === slug);
}
