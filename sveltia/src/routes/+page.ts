import { testimonials } from '$lib/data';
import { editorialExcerpt, sortTestimonials } from '$lib/home';
import { getEditorialPage } from '$lib/markdown';

export function load() {
	const teamPage = getEditorialPage('home-team');
	const approachPage = getEditorialPage('approach');

	return {
		teamSummary: teamPage?.body ?? '',
		approachSummary: approachPage
			? editorialExcerpt(approachPage.body, 'What happens in a workshop')
			: '',
		testimonials: sortTestimonials(testimonials)
	};
}
