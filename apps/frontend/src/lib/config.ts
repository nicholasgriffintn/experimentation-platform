export const API_URL = import.meta.env.API_URL || 'http://localhost:8000';

export const config = {
    api: {
        experiments: `${API_URL}/api/v1/experiments`,
        metrics: `${API_URL}/api/v1/metrics`,
        features: `${API_URL}/api/v1/features`
    }
}; 