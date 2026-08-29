import { error } from '@sveltejs/kit';
import { people, peopleById } from '$lib/data';
import { coursesForPerson } from '$lib/people';

export function entries() {
	return people.map((person) => ({ id: person.id }));
}

export function load({ params }) {
	const person = peopleById[params.id];
	if (!person) error(404, 'Person not found');
	return {
		person,
		courses: coursesForPerson(person.id)
	};
}
