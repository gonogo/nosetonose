import { people } from '$lib/data';
import { peopleSections } from '$lib/people';

export function load() {
	return { sections: peopleSections(people) };
}
