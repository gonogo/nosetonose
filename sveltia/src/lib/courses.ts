import { venuesById } from './data';
import type { Course, Venue } from './types';

export const REGION_ORDER = ['UK', 'Europe', 'North America', 'Other'] as const;

export const LEVEL_ORDER = [
	'Clown 1',
	'Clown 2',
	'Clown 3',
	'Social Clowning',
	'Masterclass',
	'Clown and Dance',
	'Courage to Be',
	'Introduction',
	'Facilitator Training',
	'Performance'
];

export function courseSlug(courseId: string): string {
	return courseId.split('/').pop() ?? courseId;
}

export function formatDate(value: string | null): string {
	if (!value) return '';
	const date = new Date(`${value}T00:00:00`);
	if (Number.isNaN(date.getTime())) return value;
	return date.toLocaleDateString('en-GB', {
		day: 'numeric',
		month: 'long',
		year: 'numeric'
	});
}

export function formatDateRange(start: string | null, end: string | null): string {
	const from = formatDate(start);
	const to = formatDate(end);
	if (from && to && from !== to) return `${from} – ${to}`;
	return from || to || 'Dates to be confirmed';
}

export function courseVenue(course: Course): Venue | undefined {
	return course.venue ? venuesById[course.venue] : undefined;
}

export function courseLocation(course: Course): string | null {
	return courseVenue(course)?.location || course.location_country;
}

export function regionAnchor(region: string): string {
	return region.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '') || 'other';
}

export function levelAnchor(level: string): string {
	return regionAnchor(level);
}

export function regionLevelAnchor(region: string, level: string): string {
	return `${regionAnchor(region)}-${levelAnchor(level)}`;
}

export function courseLevelLabel(level: string | null): string {
	return level || 'Other';
}

function levelSortKey(level: string): [number, string] {
	const index = LEVEL_ORDER.indexOf(level);
	return [index === -1 ? LEVEL_ORDER.length : index, level.toLowerCase()];
}

export function coursesByRegion(all: Course[]): { region: string; courses: Course[] }[] {
	const groups = new Map<string, Course[]>();
	for (const region of REGION_ORDER) groups.set(region, []);
	for (const course of all) {
		const region = course.region || 'Other';
		if (!groups.has(region)) groups.set(region, []);
		groups.get(region)!.push(course);
	}
	return [...groups.entries()]
		.filter(([, list]) => list.length)
		.map(([region, list]) => ({ region, courses: list }));
}

export function coursesByLevel(all: Course[]): { level: string; courses: Course[] }[] {
	const groups = new Map<string, Course[]>();
	for (const course of all) {
		const level = courseLevelLabel(course.clown_level);
		if (!groups.has(level)) groups.set(level, []);
		groups.get(level)!.push(course);
	}
	for (const list of groups.values()) {
		list.sort(
			(a, b) =>
				(a.start_date || '9999-99-99').localeCompare(b.start_date || '9999-99-99') ||
				a.title.localeCompare(b.title)
		);
	}
	return [...groups.entries()]
		.sort((a, b) => {
			const [ai, al] = levelSortKey(a[0]);
			const [bi, bl] = levelSortKey(b[0]);
			return ai - bi || al.localeCompare(bl);
		})
		.map(([level, list]) => ({ level, courses: list }));
}

export function findCourseBySlug(all: Course[], slug: string): Course | undefined {
	return all.find((course) => courseSlug(course.id) === slug);
}

export function countLabel(count: number, noun: string): string {
	return `${count} ${noun}${count === 1 ? '' : 's'}.`;
}
