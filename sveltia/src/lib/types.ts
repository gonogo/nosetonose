export type Region = 'UK' | 'Europe' | 'North America';
export type Medium = 'In-person' | 'Online';
export type PersonType = 'team-facilitator' | 'associate-facilitator' | 'team-passed-away';
export type PersonStatus = 'active' | 'previous-associate';

export type CourseType = {
	id: string;
	title: string;
	clown_level: string | null;
	prerequisites: string | null;
	medium: Medium;
	maximum_group_size: number | null;
	course_fee: string | null;
	course_fee_deposit: string | null;
	facilitators: string[];
	schedule: string | null;
	course_description: string | null;
};

export type Event = {
	id: string;
	title: string;
	source_url: string;
	course: string | null;
	start_date: string | null;
	end_date: string | null;
	location_country: string | null;
	region: Region | null;
	venue: string | null;
	language: string | null;
	facilitators: string[];
	clown_level: string | null;
	prerequisites: string | null;
	medium: Medium | null;
	maximum_group_size: number | null;
	course_fee: string | null;
	course_fee_deposit: string | null;
	schedule: string | null;
	course_description: string | null;
	accommodation_and_meals: string | null;
};

/** Event with course-type fields merged in for display. */
export type Course = Event & {
	course_title: string;
	medium: Medium;
};

export type Venue = {
	id: string;
	name: string;
	address: string | null;
	location: string | null;
	email: string | null;
	phone: string | null;
};

export type Person = {
	id: string;
	name: string;
	person_type: PersonType;
	status: PersonStatus;
	background: string | null;
	photo: string | null;
	country: string | null;
	region: Region | null;
	source_urls?: string[];
};

export type EditorialPage = {
	slug: string;
	title: string;
	body: string;
};

export type Article = {
	slug: string;
	title: string;
	source_url: string | null;
	body: string;
};

export type Testimonial = {
	id: string;
	title: string;
	source_url: string | null;
	date: string | null;
	quote: string | null;
};
