import { courseTypesById, events, venuesById } from './data';
import type { Course, CourseType, Event, Venue } from './types';

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

function inheritString(eventVal: string | null, courseVal: string | null | undefined): string | null {
	return eventVal || courseVal || null;
}

function inheritNumber(eventVal: number | null, courseVal: number | null | undefined): number | null {
	return eventVal ?? courseVal ?? null;
}

function inheritList(eventVal: string[], courseVal: string[] | undefined): string[] {
	return eventVal.length ? eventVal : (courseVal ?? []);
}

export function resolveListing(event: Event, typesById: Record<string, CourseType> = courseTypesById): Course {
	const courseType = event.course ? typesById[event.course] : undefined;
	return {
		...event,
		course_title: courseType?.title ?? event.title,
		clown_level: inheritString(event.clown_level, courseType?.clown_level),
		prerequisites: inheritString(event.prerequisites, courseType?.prerequisites),
		medium: event.medium ?? courseType?.medium ?? 'In-person',
		maximum_group_size: inheritNumber(event.maximum_group_size, courseType?.maximum_group_size),
		course_fee: inheritString(event.course_fee, courseType?.course_fee),
		course_fee_deposit: inheritString(event.course_fee_deposit, courseType?.course_fee_deposit),
		facilitators: inheritList(event.facilitators, courseType?.facilitators),
		schedule: inheritString(event.schedule, courseType?.schedule),
		course_description: inheritString(event.course_description, courseType?.course_description)
	};
}

export const courses = events.map((event) => resolveListing(event));

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
	return [...groups.entries()]
		.sort((a, b) => {
			const [ai, al] = levelSortKey(a[0]);
			const [bi, bl] = levelSortKey(b[0]);
			return ai - bi || al.localeCompare(bl);
		})
		.map(([level, list]) => ({ level, courses: list }));
}

export function coursesByCourseTitle(all: Course[]): { title: string; courses: Course[] }[] {
	const groups = new Map<string, Course[]>();
	for (const course of all) {
		const title = course.course_title;
		if (!groups.has(title)) groups.set(title, []);
		groups.get(title)!.push(course);
	}
	for (const list of groups.values()) {
		list.sort(
			(a, b) =>
				(a.start_date || '9999-99-99').localeCompare(b.start_date || '9999-99-99') ||
				a.title.localeCompare(b.title)
		);
	}
	return [...groups.entries()]
		.sort((a, b) => a[0].localeCompare(b[0], undefined, { sensitivity: 'base' }))
		.map(([title, list]) => ({ title, courses: list }));
}

export function findCourseBySlug(all: Course[], slug: string): Course | undefined {
	return all.find((course) => courseSlug(course.id) === slug);
}

export function countLabel(count: number, noun: string): string {
	return `${count} ${noun}${count === 1 ? '' : 's'}.`;
}
