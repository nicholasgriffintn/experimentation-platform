import { config } from '../config';

export class APIError extends Error {
    constructor(
        public status: number,
        public statusText: string,
        public data: any
    ) {
        super(`${status} ${statusText}`);
        this.name = 'APIError';
    }
}

export class BaseAPI {
    protected baseUrl: string;

    constructor(path: string) {
        this.baseUrl = `${config.apiBaseUrl}/api/v1${path}`;
    }

    protected async request<T>(
        endpoint: string,
        options: RequestInit = {}
    ): Promise<T> {
        const response = await fetch(`${this.baseUrl}${endpoint}`, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers,
            },
            credentials: 'include',
            ...options,
        });

        const data = await response.json();

        if (!response.ok) {
            throw new APIError(
                response.status,
                response.statusText,
                data
            );
        }

        return data as T;
    }

    protected async get<T>(endpoint: string): Promise<T> {
        return this.request<T>(endpoint);
    }

    protected async post<T>(endpoint: string, body: any): Promise<T> {
        return this.request<T>(endpoint, {
            method: 'POST',
            body: JSON.stringify(body),
        });
    }

    protected async put<T>(endpoint: string, body: any): Promise<T> {
        return this.request<T>(endpoint, {
            method: 'PUT',
            body: JSON.stringify(body),
        });
    }

    protected async delete(endpoint: string): Promise<void> {
        await this.request(endpoint, {
            method: 'DELETE',
        });
    }
} 