import matplotlib.pyplot as plt
import seaborn as sns
import tempfile


def plot_uplift_distribution(uplift_dist, uplift_method, figsize=(18, 6)):
    """Plot the uplift distribution and cumulative distribution."""
    sns.set_style("whitegrid")
    plt.figure(figsize=figsize)

    # Uplift distribution
    plt.subplot(1, 2, 1)
    plt.title("Uplift Distribution")
    ax = sns.kdeplot(uplift_dist, fill=True, color="black")

    if ax.lines:
        kde_x, kde_y = ax.lines[0].get_data()
        cutoff = 1 if uplift_method == "ratio" else 0

        plt.axvline(x=cutoff, linestyle="--", color="black")
        plt.fill_between(
            kde_x, kde_y, where=(kde_x <= cutoff), color="orange", alpha=0.6
        )
        plt.fill_between(
            kde_x, kde_y, where=(kde_x > cutoff), color="lightgreen", alpha=0.6
        )

    plt.xlabel("Uplift")
    plt.ylabel("Density")

    # Cumulative distribution
    plt.subplot(1, 2, 2)
    plt.title("Cumulative Uplift Distribution")
    sns.kdeplot(uplift_dist, cumulative=True, color="blue", fill=True)
    plt.xlabel("Cumulative Uplift")
    plt.ylabel("Density")

    # Save the plot to a temporary file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    plt.savefig(temp_file.name, format="png")
    plt.close()

    return temp_file.name
