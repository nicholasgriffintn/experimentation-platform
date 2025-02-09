export interface UserContext {
    user_id: string;
    properties?: Record<string, any>;
}

export interface MetricDefinition {
    name: string;
    description: string;
    unit: string;
    data_type: 'continuous' | 'binary' | 'count' | 'ratio';
    aggregation_method: string;
    query_template: string;
    min_sample_size?: number;
    min_effect_size?: number;
}

export interface Variant {
    id: string;
    name: string;
    type: 'control' | 'treatment' | 'feature_flag';
    config: Record<string, any>;
    traffic_percentage: number;
}

export interface ExperimentSchedule {
    start_time: string;
    end_time?: string;
    ramp_up_period?: number;
    auto_stop_conditions?: Record<string, any>;
}

export interface ExperimentCreate {
    name: string;
    description: string;
    type: 'ab_test' | 'multivariate' | 'feature_flag';
    hypothesis?: string;
    metrics: string[];
    variants: Omit<Variant, 'id'>[];
    targeting_rules?: Record<string, any>;
    schedule?: ExperimentSchedule;
    parameters?: Record<string, any>;
}

export interface Experiment extends ExperimentCreate {
    id: string;
    status: 'draft' | 'scheduled' | 'running' | 'paused' | 'completed' | 'stopped';
    created_at: string;
    updated_at: string;
    started_at?: string;
    ended_at?: string;
    stopped_reason?: string;
}

export interface VariantAssignment {
    experiment_id: string;
    variant_id: string;
    variant_name: string;
    config: Record<string, any>;
}

export interface MetricResult {
    metric_name: string;
    variant_id: string;
    value: number;
    confidence_interval?: [number, number];
    sample_size: number;
}

export interface ExperimentResults {
    experiment_id: string;
    metrics: MetricResult[];
    last_updated: string;
} 