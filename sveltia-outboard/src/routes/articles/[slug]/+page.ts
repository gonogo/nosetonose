import { error } from '@sveltejs/kit';
import { articles, getArticle } from '$lib/markdown';

export function entries() {
	return articles.map((article) => ({ slug: article.slug }));
}

export function load({ params }) {
	const article = getArticle(params.slug);
	if (!article) error(404, 'Article not found');
	return article;
}
