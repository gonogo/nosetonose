<script lang="ts">
	import { afterNavigate } from '$app/navigation';
	import { page } from '$app/state';

	let open = $state(false);
	const path = $derived(page.url.pathname);

	afterNavigate(() => {
		open = false;
	});

	function isCurrent(href: string, extra: string[] = []): boolean {
		if (href === '/') return path === '/';
		if (href === '/courses') return path === '/courses' || path.startsWith('/courses/');
		return path === href || path.startsWith(`${href}/`) || extra.some((item) => path.startsWith(item));
	}

	const trainingOpen = $derived(path === '/training' || path.startsWith('/training/'));
</script>

<header class="site-header" class:nav-open={open}>
	<div class="site-header-inner">
		<a class="wordmark" href="/">
			<span class="nose" aria-hidden="true"></span>
			Nose to Nose
		</a>
		<button
			class="menu-toggle"
			type="button"
			aria-expanded={open}
			aria-controls="site-nav"
			onclick={() => (open = !open)}
		>
			{open ? 'Close' : 'Menu'}
		</button>
		<nav class="site-nav" id="site-nav" aria-label="Site">
			<ul>
				<li>
					<a href="/" aria-current={isCurrent('/') ? 'page' : undefined}>Home</a>
				</li>
				<li>
					<a href="/courses" aria-current={isCurrent('/courses') ? 'page' : undefined}>Courses</a>
				</li>
				<li>
					<a href="/approach" aria-current={isCurrent('/approach') ? 'page' : undefined}>Approach</a>
				</li>
				<li class="has-sub" data-active={trainingOpen}>
					<a class="nav-parent" href="/training" aria-current={trainingOpen ? 'page' : undefined}
						>Training</a
					>
					<ul class="subnav">
						<li>
							<a
								href="/training/clown-programme"
								aria-current={isCurrent('/training/clown-programme') ? 'page' : undefined}
								>Clown programme</a
							>
						</li>
						<li>
							<a
								href="/training/for-organisations"
								aria-current={isCurrent('/training/for-organisations') ? 'page' : undefined}
								>For organisations</a
							>
						</li>
					</ul>
				</li>
				<li>
					<a href="/how-to-book" aria-current={isCurrent('/how-to-book') ? 'page' : undefined}
						>How to book</a
					>
				</li>
				<li>
					<a href="/team" aria-current={isCurrent('/team') ? 'page' : undefined}>Team</a>
				</li>
				<li>
					<a href="/articles" aria-current={isCurrent('/articles') ? 'page' : undefined}>Articles</a>
				</li>
				<li>
					<a href="/contact" aria-current={isCurrent('/contact') ? 'page' : undefined}>Contact us</a>
				</li>
			</ul>
		</nav>
	</div>
</header>
