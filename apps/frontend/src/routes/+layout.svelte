<script lang="ts">
	import '../app.postcss';
	import { page } from '$app/stores';
	import NavLink from '../components/common/NavLink.svelte';
</script>

<div class="min-h-screen bg-gray-50">
	<nav class="bg-white shadow">
		<div class="container mx-auto px-4">
			<div class="flex justify-between h-16">
				<div class="flex">
					<div class="flex-shrink-0 flex items-center">
						<a href="/" class="text-xl font-bold text-gray-800">
							ExP Platform
						</a>
					</div>

					<div class="hidden sm:ml-6 sm:flex sm:space-x-8">
						<NavLink
							href="/"
							active={$page.url.pathname === '/'}
						>
							Dashboard
						</NavLink>
						<NavLink
							href="/experiments"
							active={$page.url.pathname.startsWith('/experiments')}
						>
							Experiments
						</NavLink>
						<NavLink
							href="/metrics"
							active={$page.url.pathname.startsWith('/metrics')}
						>
							Metrics
						</NavLink>
					</div>
				</div>
			</div>
		</div>
	</nav>


	<main>
		<slot />
	</main>
</div> 