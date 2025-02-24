# Experimentation Platform Demo

This repository contains demo applications for interacting with the Experimentation Platform API. These demos showcase how to implement A/B tests, multivariate tests, and feature flags in web applications, including:

1. Assigning users to experiment variants
2. Recording experiment exposures
3. Submitting metric events
4. Viewing experiment results

## Demo Applications

### Demo App

An interactive UI for testing experiment functionality on a user-by-user basis:

- Configure user context and attributes
- Assign users to experiment variants
- Record exposures when users see experiment treatments
- Submit metric events to track experiment performance
- View experiment results and statistical significance

### Traffic Simulator

A tool to generate realistic user traffic to automatically populate experiments with data:

- Simulate hundreds of users with different attributes
- Generate realistic variant assignments based on targeting rules
- Automatically record exposures and metrics
- Build up experiment results for analysis

## Example Use Cases

The demo apps work with the seeded experiments, which include:

1. **Button Color Test**: Simple A/B test of button colors
2. **Homepage Layout Optimization**: Multivariate test with different layouts and images
3. **New Checkout Flow**: Feature flag test for a new checkout process
4. **Price Sensitivity Test**: Testing impact of price reduction on revenue
5. **New User Onboarding Flow**: Testing simplified onboarding

## Running the Demo Apps

1. Install dependencies:

   ```bash
   pnpm install
   ```

2. Start the server:
   ```bash
   pnpm start
   ```
