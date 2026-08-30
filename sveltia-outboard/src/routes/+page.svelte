<script lang="ts">
	import Markdown from '$lib/components/Markdown.svelte';
	import { NEWSLETTER_URL } from '$lib/home';
	import type { Testimonial } from '$lib/types';

	let {
		data
	}: {
		data: {
			teamSummary: string;
			approachSummary: string;
			testimonials: Testimonial[];
		};
	} = $props();
</script>

<svelte:head>
	<title>Nose to Nose — clown workshops and training</title>
</svelte:head>

<main class="site-main home-page">
	<header class="home-hero">
		<h1>Nose to Nose</h1>
		<p class="page-intro">
			Clown workshops and facilitator training in the UK, Europe, and North America. Small groups,
			in person and online.
		</p>
		<p class="home-hero-links">
			<a class="button-link" href="/courses">Browse courses</a>
			<a class="text-link" href="/how-to-book">How to book</a>
		</p>
	</header>

	<section class="home-section" aria-labelledby="about-heading">
		<h2 id="about-heading">About us</h2>
		<div class="prose home-prose">
			<Markdown source={data.teamSummary} />
		</div>
		<p class="section-link"><a href="/team">Meet the team</a></p>
	</section>

	<section class="home-section" aria-labelledby="approach-heading">
		<h2 id="approach-heading">Our approach</h2>
		<div class="prose home-prose">
			<Markdown source={data.approachSummary} />
		</div>
		<p class="section-link"><a href="/approach">Read our full approach</a></p>
	</section>

	<section class="home-section newsletter-section" aria-labelledby="newsletter-heading">
		<h2 id="newsletter-heading">Join our mailing list</h2>
		<p class="newsletter-intro">
			Receive our newsletter twice a year with course updates and news. You can unsubscribe at any
			time. We do not share our mailing list.
		</p>
		<form
			class="newsletter-form"
			action={NEWSLETTER_URL}
			method="get"
			target="_blank"
			rel="noopener noreferrer"
		>
			<label class="visually-hidden" for="newsletter-email">Email address</label>
			<input
				id="newsletter-email"
				name="email"
				type="email"
				autocomplete="email"
				placeholder="you@example.com"
				required
			/>
			<button type="submit">Sign up</button>
		</form>
	</section>

	<section class="home-section testimonials-section" aria-labelledby="testimonials-heading">
		<h2 id="testimonials-heading">Testimonials</h2>
		{#if data.testimonials.length}
			<ul class="testimonial-list">
				{#each data.testimonials as testimonial (testimonial.id)}
					<li class="testimonial-card">
						{#if testimonial.quote}
							<div class="testimonial-quote prose">
								<Markdown source={testimonial.quote} />
							</div>
						{/if}
						<p class="testimonial-attribution">{testimonial.title}</p>
					</li>
				{/each}
			</ul>
		{:else}
			<p class="meta">No testimonials yet.</p>
		{/if}
	</section>
</main>
