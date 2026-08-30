import { courseTypesById, events, venuesById } from './data';
import { getEditorialPage } from './markdown';
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

function parseDay(value: string | null): Date | null {
	if (!value) return null;
	const date = new Date(`${value}T00:00:00`);
	return Number.isNaN(date.getTime()) ? null : date;
}

const MONTH_YEAR = new Intl.DateTimeFormat('en-GB', { month: 'long', year: 'numeric' });
const MONTH = new Intl.DateTimeFormat('en-GB', { month: 'long' });

export function formatDate(value: string | null): string {
	const date = parseDay(value);
	if (!date) return value || '';
	return date.toLocaleDateString('en-GB', {
		day: 'numeric',
		month: 'long',
		year: 'numeric'
	});
}

export function formatDateRange(start: string | null, end: string | null): string {
	const from = parseDay(start);
	const to = parseDay(end);
	if (!from && !to) return 'Dates to be confirmed';
	if (!to || (from && from.getTime() === to.getTime())) return formatDate(start);
	if (!from) return formatDate(end);
	if (from.getFullYear() === to.getFullYear() && from.getMonth() === to.getMonth()) {
		return `${from.getDate()}–${to.getDate()} ${MONTH_YEAR.format(to)}`;
	}
	if (from.getFullYear() === to.getFullYear()) {
		return `${from.getDate()} ${MONTH.format(from)} – ${to.getDate()} ${MONTH_YEAR.format(to)}`;
	}
	return `${formatDate(start)} – ${formatDate(end)}`;
}

export function courseVenue(course: Course): Venue | undefined {
	return course.venue ? venuesById[course.venue] : undefined;
}

export function courseLocation(course: Course): string | null {
	return courseVenue(course)?.location || course.location_country;
}

/** Place shown on a listing row. Online runs omit country so “Online” can stand alone. */
export function courseInstancePlace(course: Course): string | null {
	if (course.medium === 'Online') return null;
	return courseLocation(course);
}

function stripMarkdownInline(text: string): string {
	return text
		.replace(/^#{1,6}\s+/gm, '')
		.replace(/^>\s+/gm, '')
		.replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
		.replace(/[*_]{1,3}([^*_]+)[*_]{1,3}/g, '$1')
		.replace(/\s+/g, ' ')
		.trim();
}

function isJunkSummary(text: string): boolean {
	if (text.length < 40) return true;
	if (
		/^(with |avec |january |february |march |april |may |june |july |august |september |october |november |december |an online course|nb\b|this course is now|the word )/i.test(
			text
		)
	) {
		return true;
	}
	if (/^[“”"'*#>\d]/.test(text)) return true;
	const letters = text.replace(/[^a-zA-ZÀ-ÿ]/g, '');
	const upper = text.replace(/[^A-ZÀ-Ÿ]/g, '');
	return letters.length >= 20 && upper.length / letters.length > 0.55;
}

const PREFERRED_SUMMARY = /^(this course|join |an intensive|in this |a course |a weekend)/i;

/** Short listing blurb from a course description: first real sentence, no images or credits. */
export function listingSummary(description: string | null): string | null {
	if (!description) return null;
	let cleaned = description.trim();
	cleaned = cleaned.replace(/^(?:\[!\[[^\]]*\]\([^)]+\)\]\([^)]+\)\s*)+/, '');
	cleaned = cleaned.replace(/^(?:!\[[^\]]*\]\([^)]+\)\s*)+/, '');
	cleaned = cleaned.replace(/!\[[^\]]*\]\([^)]+\)/g, ' ');

	const sentences: string[] = [];
	for (const block of cleaned.split(/\n\s*\n/)) {
		const paragraph = stripMarkdownInline(
			block.replace(/\s*The group is limited to \d+\.?/gi, ' ')
		);
		if (!paragraph) continue;
		const parts = paragraph.match(/[^.!?]+[.!?]+(?:\s+|$)|[^.!?]+$/g) ?? [paragraph];
		for (const part of parts) {
			const sentence = part.replace(/^[“”"']+|["”']+$/g, '').trim();
			if (!isJunkSummary(sentence)) sentences.push(sentence);
		}
	}

	const chosen = sentences.find((sentence) => PREFERRED_SUMMARY.test(sentence)) ?? sentences[0];
	if (!chosen) return null;
	if (chosen.length <= 160) return chosen;
	const cut = chosen.slice(0, 157);
	const at = cut.lastIndexOf(' ');
	return `${cut.slice(0, at > 80 ? at : 157)}…`;
}

/** Index blurbs come from the course type, not venue-specific listing copy. */
export function courseGroupSummary(group: Course[]): string | null {
	const typeId = group.find((course) => course.course)?.course;
	if (!typeId) return null;
	return listingSummary(courseTypesById[typeId]?.course_description ?? null);
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

function parseMarkdownSections(body: string): Map<string, string> {
	const sections = new Map<string, string>();
	const matches = [...body.matchAll(/^### (.+)$/gm)];
	for (let i = 0; i < matches.length; i++) {
		const heading = matches[i][1].trim();
		const start = matches[i].index! + matches[i][0].length;
		const end = i + 1 < matches.length ? matches[i + 1].index! : body.length;
		const firstParagraph = body.slice(start, end).trim().split(/\n\s*\n/)[0]?.trim() ?? '';
		if (firstParagraph) sections.set(heading.toLowerCase(), firstParagraph);
	}
	return sections;
}

function findProgrammeSection(sections: Map<string, string>, ...headings: string[]): string | null {
	for (const heading of headings) {
		const key = heading.toLowerCase();
		if (sections.has(key)) return sections.get(key)!;
		for (const [sectionHeading, text] of sections) {
			if (sectionHeading.startsWith(key)) return text;
		}
	}
	return null;
}

function buildLevelSummaries(): Record<string, string> {
	const body = getEditorialPage('clown-programme')?.body ?? '';
	const sections = parseMarkdownSections(body);
	const summaries: Record<string, string> = {};
	const mappings: [string, ...string[]][] = [
		['Clown 1', 'Level 1'],
		['Clown 2', 'Level 2'],
		['Clown 3', 'Level 3'],
		['Performance', 'Towards Performance'],
		['Social Clowning', 'Social clowning'],
		['Introduction', 'Introductory']
	];
	for (const [level, ...headings] of mappings) {
		const summary = findProgrammeSection(sections, ...headings);
		if (summary) summaries[level] = summary;
	}
	return summaries;
}

const LEVEL_SUMMARIES = buildLevelSummaries();

/** First paragraph from the matching section on the clown programme page. */
export function levelSummary(level: string): string | null {
	return LEVEL_SUMMARIES[level] ?? null;
}
