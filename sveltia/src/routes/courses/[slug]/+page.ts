import { error } from '@sveltejs/kit';
import { courses, peopleById, venuesById } from '$lib/data';
import { courseSlug, findCourseBySlug } from '$lib/courses';

export function entries() {
	return courses.map((course) => ({ slug: courseSlug(course.id) }));
}

export function load({ params }) {
	const course = findCourseBySlug(courses, params.slug);
	if (!course) error(404, 'Course not found');
	return {
		course,
		venue: course.venue ? venuesById[course.venue] ?? null : null,
		facilitators: course.facilitators
			.map((id) => peopleById[id])
			.filter((person): person is NonNullable<typeof person> => Boolean(person))
	};
}
