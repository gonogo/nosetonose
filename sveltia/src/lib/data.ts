import type { Course, Person, Region, Testimonial, Venue } from './types';

function emptyToNull(value: unknown): string | null {
	if (value == null) return null;
	const text = String(value).trim();
	return text === '' ? null : text;
}

function stringList(value: unknown): string[] | undefined {
	if (!Array.isArray(value)) return undefined;
	const items = value
		.map((item) => {
			if (typeof item === 'string') return item.trim();
			if (item && typeof item === 'object' && 'url' in item) {
				return String((item as { url: unknown }).url).trim();
			}
			return '';
		})
		.filter(Boolean);
	return items.length ? items : undefined;
}

function asCourse(raw: Course): Course {
	const region = emptyToNull(raw.region);
	return {
		...raw,
		start_date: emptyToNull(raw.start_date),
		end_date: emptyToNull(raw.end_date),
		location_country: emptyToNull(raw.location_country),
		region: region === 'UK' || region === 'Europe' || region === 'North America' ? region : null,
		venue: emptyToNull(raw.venue),
		language: emptyToNull(raw.language),
		facilitators: Array.isArray(raw.facilitators) ? raw.facilitators.filter(Boolean) : [],
		clown_level: emptyToNull(raw.clown_level),
		prerequisites: emptyToNull(raw.prerequisites),
		medium: raw.medium === 'Online' ? 'Online' : 'In-person',
		maximum_group_size:
			typeof raw.maximum_group_size === 'number' ? raw.maximum_group_size : null,
		course_fee: emptyToNull(raw.course_fee),
		course_fee_deposit: emptyToNull(raw.course_fee_deposit),
		schedule: emptyToNull(raw.schedule),
		course_description: emptyToNull(raw.course_description),
		accommodation_and_meals: emptyToNull(raw.accommodation_and_meals)
	};
}

function asVenue(raw: Venue): Venue {
	return {
		...raw,
		address: emptyToNull(raw.address),
		location: emptyToNull(raw.location),
		email: emptyToNull(raw.email),
		phone: emptyToNull(raw.phone)
	};
}

function asPerson(raw: Person): Person {
	const region = emptyToNull(raw.region);
	return {
		...raw,
		background: emptyToNull(raw.background),
		photo: emptyToNull(raw.photo),
		country: emptyToNull(raw.country),
		region: (region === 'UK' || region === 'Europe' || region === 'North America'
			? region
			: null) as Region | null,
		source_urls: stringList(raw.source_urls)
	};
}

function asTestimonial(raw: Testimonial): Testimonial {
	return {
		...raw,
		source_url: emptyToNull(raw.source_url),
		date: emptyToNull(raw.date),
		quote: emptyToNull(raw.quote)
	};
}

const courseModules = import.meta.glob('./data/courses/*.json', {
	eager: true,
	import: 'default'
}) as Record<string, Course>;

const venueModules = import.meta.glob('./data/venues/*.json', {
	eager: true,
	import: 'default'
}) as Record<string, Venue>;

const peopleModules = import.meta.glob('./data/people/*.json', {
	eager: true,
	import: 'default'
}) as Record<string, Person>;

const testimonialModules = import.meta.glob('./data/testimonials/*.json', {
	eager: true,
	import: 'default'
}) as Record<string, Testimonial>;

export const courses = Object.values(courseModules).map(asCourse);
export const venues = Object.values(venueModules).map(asVenue);
export const people = Object.values(peopleModules).map(asPerson);
export const testimonials = Object.values(testimonialModules).map(asTestimonial);

export const venuesById: Record<string, Venue> = Object.fromEntries(
	venues.map((venue) => [venue.id, venue])
);

export const peopleById: Record<string, Person> = Object.fromEntries(
	people.map((person) => [person.id, person])
);

export const testimonialsById: Record<string, Testimonial> = Object.fromEntries(
	testimonials.map((testimonial) => [testimonial.id, testimonial])
);
