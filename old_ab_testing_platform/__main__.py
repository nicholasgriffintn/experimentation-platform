import click

from .lib.utils import load_user_data, parse_group_buckets
from .pipeline import run_experiment


@click.group()
def cli():
    """
    pipeline commands
    """


@cli.group()
def ab_testing():
    """
    AB Testing commands
    """


def display_results(results):
    if "error" in results:
        click.echo(results["error"], err=True)
        return

    method = results["method"]
    result = results["results"]

    if method == "frequentist":
        for test_group, res in result.items():
            click.echo(f"\nFrequentist Test Results for {test_group}\n{'='*25}")
            click.echo(f"Test Statistic (Z): {res['statistic']:.4f}")
            click.echo(f"P-Value: {res['p_value']:.4f}")
            click.echo(
                f"Control Successes: {res['control_success']} / {res['control_trials']}"
            )
            click.echo(f"Test Successes: {res['test_success']} / {res['test_trials']}")

        if "corrected_p_values" in results:
            click.echo(
                f"\nCorrected P-Values using {results['correction_method']} method\n{'='*50}"
            )
            for test_group, corrected_p_value in results["corrected_p_values"].items():
                click.echo(f"{test_group}: {corrected_p_value:.4f}")
        else:
            click.echo(
                "\nNo multiple testing correction applied as only one test was conducted."
            )

    else:
        for test_group, res in result.items():
            click.echo(f"\nBayesian Test Results for {test_group}\n{'='*25}")
            click.echo(
                f"Control Successes: {res['control_success']} / {res['control_trials']}"
            )
            click.echo(f"Test Successes: {res['test_success']} / {res['test_trials']}")


def get_experiment_parameters():
    method = click.prompt("Choose testing method: 'frequentist' or 'bayesian'")
    if method == "frequentist":
        alpha = click.prompt(
            "Enter alpha (significance level)", type=float, default=0.05
        )
        return method, alpha, None, None
    else:
        prior_successes = click.prompt(
            "Enter prior successes for Bayesian", type=int, default=30
        )
        prior_trials = click.prompt(
            "Enter prior trials for Bayesian", type=int, default=100
        )
        return method, None, prior_successes, prior_trials


@click.command()
@click.option(
    "--group_buckets",
    required=True,
    type=str,
    help="Group buckets in the format 'group1:start-end,group2:start-end' (e.g., 'control:0-50,test1:50-100')",
    default="control:0-50,test1:50-100",
)
def input_data_manually(group_buckets):
    """
    Input user data manually and run an A/B test.
    """
    user_data = []
    while True:
        user_id = click.prompt("Enter User ID (or 'q' to quit)")
        if user_id == "q":
            break
        event = click.prompt(
            f"Did User {user_id} succeed? (1 for yes, 0 for no)", type=int
        )
        user_data.append({"user_id": user_id, "event": event})

    click.echo(f"Collected {len(user_data)} users. Now running the experiment.")
    group_buckets_dict = parse_group_buckets(group_buckets)
    click.echo(f"Using group buckets: {group_buckets_dict}")

    method, alpha, prior_successes, prior_trials = get_experiment_parameters()
    results = run_experiment(
        user_data=user_data,
        group_buckets=group_buckets_dict,
        method=method,
        alpha=alpha,
        prior_successes=prior_successes,
        prior_trials=prior_trials,
    )

    display_results(results)


ab_testing.add_command(input_data_manually)


@click.command()
@click.option(
    "--file_path",
    required=True,
    type=click.Path(exists=True),
    help="The path to the JSON file containing user data",
    default="./tests/fixtures/ab-testing-users.json",
)
@click.option(
    "--group_buckets",
    required=True,
    type=str,
    help="Group buckets in the format 'group1:start-end,group2:start-end' (e.g., 'control:0-50,test1:50-100')",
    default="control:0-50,test1:50-100",
)
def load_data_from_file(file_path: str, group_buckets: str):
    """
    Load user data from a JSON file and run an A/B test.
    """
    try:
        user_data = load_user_data(file_path)
        click.echo(
            f"Loaded {len(user_data)} users from {file_path}. Now running the experiment."
        )
        group_buckets_dict = parse_group_buckets(group_buckets)
        click.echo(f"Using group buckets: {group_buckets_dict}")

        method, alpha, prior_successes, prior_trials = get_experiment_parameters()
        results = run_experiment(
            user_data=user_data,
            group_buckets=group_buckets_dict,
            method=method,
            alpha=alpha,
            prior_successes=prior_successes,
            prior_trials=prior_trials,
        )

        display_results(results)

    except Exception as e:
        click.echo(f"Error loading file: {e}", err=True)


ab_testing.add_command(load_data_from_file)


if __name__ == "__main__":
    cli()
