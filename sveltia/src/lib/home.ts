import type { Testimonial } from './types';

export const NEWSLETTER_URL =
	'https://go.reachmail.net/SubscriptionForm/2b462544-0262-4f80-9928-aa4400d56563';

export function editorialExcerpt(body: string, untilHeading: string): string {
	const marker = `# ${untilHeading}`;
	const idx = body.indexOf(marker);
	const excerpt = idx === -1 ? body : body.slice(0, idx);
	return excerpt.replace(/^#\s+.+(\r?\n)+/, '').trim();
}

export function sortTestimonials(testimonials: Testimonial[]): Testimonial[] {
	return [...testimonials].sort((a, b) => {
		const ad = a.date || '';
		const bd = b.date || '';
		if (ad !== bd) return bd.localeCompare(ad);
		return a.title.localeCompare(b.title);
	});
}
