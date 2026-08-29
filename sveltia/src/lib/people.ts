import { REGION_ORDER, courses } from './courses';
import type { Course, Person } from './types';

export function personDisplayLabel(person: Person): string {
	if (
		(person.person_type === 'team-facilitator' ||
			person.person_type === 'associate-facilitator') &&
		person.status === 'previous-associate'
	) {
		return 'Previous associate';
	}
	const labels: Record<Person['person_type'], string> = {
		'team-facilitator': 'Team facilitator',
		'associate-facilitator': 'Associate facilitator',
		'team-passed-away': 'In memory'
	};
	return labels[person.person_type];
}

export function peopleByType(all: Person[]) {
	const groups = {
		'team-facilitator': [] as Person[],
		'associate-facilitator': [] as Person[],
		'previous-associate': [] as Person[],
		'team-passed-away': [] as Person[]
	};
	for (const person of all) {
		if (person.person_type === 'team-passed-away') {
			groups['team-passed-away'].push(person);
		} else if (person.status === 'previous-associate') {
			groups['previous-associate'].push(person);
		} else if (person.person_type === 'team-facilitator') {
			groups['team-facilitator'].push(person);
		} else if (person.person_type === 'associate-facilitator') {
			groups['associate-facilitator'].push(person);
		}
	}
	return groups;
}

export function peopleByRegion(all: Person[]): { region: string; people: Person[] }[] {
	const groups = new Map<string, Person[]>();
	for (const region of REGION_ORDER) groups.set(region, []);
	for (const person of all) {
		const region = person.region || 'Other';
		if (!groups.has(region)) groups.set(region, []);
		groups.get(region)!.push(person);
	}
	for (const list of groups.values()) {
		list.sort((a, b) => a.name.localeCompare(b.name));
	}
	return [...groups.entries()]
		.filter(([, list]) => list.length)
		.map(([region, list]) => ({ region, people: list }));
}

export function peopleRegionAnchor(sectionId: string, region: string): string {
	return `${sectionId}-${region.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '')}`;
}

export function coursesForPerson(personId: string): Course[] {
	return courses
		.filter((course) => course.facilitators.includes(personId))
		.sort(
			(a, b) =>
				(a.start_date || '9999-99-99').localeCompare(b.start_date || '9999-99-99') ||
				a.title.localeCompare(b.title)
		);
}

export function stripLeadingImages(text: string | null): string | null {
	if (!text) return text;
	let cleaned = text.trim();
	cleaned = cleaned.replace(/^(?:\[!\[[^\]]*\]\([^)]+\)\]\([^)]+\)\s*)+/, '');
	cleaned = cleaned.replace(/^(?:!\[[^\]]*\]\([^)]+\)\s*)+/, '');
	return cleaned.trim() || null;
}

export function firstParagraph(text: string | null): string | null {
	const cleaned = stripLeadingImages(text);
	if (!cleaned) return null;
	const block = cleaned
		.split(/\n\s*\n/)
		.map((paragraph) => paragraph.trim())
		.find(Boolean);
	return block ?? null;
}

export function peopleSections(all: Person[]) {
	const groups = peopleByType(all);
	return [
		{
			id: 'team-facilitators' as const,
			heading: 'Team facilitators',
			description:
				'Facilitators listed on Nose to Nose team pages, grouped by the region they work in.',
			groupByRegion: true,
			people: groups['team-facilitator']
		},
		{
			id: 'associate-facilitators' as const,
			heading: 'Associate facilitators',
			description: 'Facilitators who lead courses but are not on the core team pages.',
			groupByRegion: true,
			people: groups['associate-facilitator']
		},
		{
			id: 'previous-associates' as const,
			heading: 'Previous associates',
			description:
				'People who completed facilitator training but no longer facilitate with Nose to Nose.',
			groupByRegion: false,
			people: [...groups['previous-associate']].sort((a, b) => a.name.localeCompare(b.name))
		},
		{
			id: 'in-memory' as const,
			heading: 'In memory',
			description: 'People remembered on the site.',
			groupByRegion: false,
			people: [...groups['team-passed-away']].sort((a, b) => a.name.localeCompare(b.name))
		}
	].filter((section) => section.people.length);
}
