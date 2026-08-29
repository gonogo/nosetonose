import { error } from '@sveltejs/kit';
import { getEditorialPage } from '$lib/markdown';

export function loadEditorial(slug: string) {
	const page = getEditorialPage(slug);
	if (!page) error(404, 'Page not found');
	return page;
}
