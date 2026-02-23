import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs));
}

export function getSeverityColor(severity: string) {
    switch (severity) {
        case 'CRITICAL':
            return 'text-severity-critical';
        case 'HIGH':
            return 'text-severity-high';
        case 'MEDIUM':
            return 'text-severity-medium';
        case 'LOW':
            return 'text-severity-low';
        case 'INFO':
            return 'text-severity-info';
        default:
            return 'text-neuro-text-muted';
    }
}

export function formatDate(value: string | number | Date) {
    const date = value instanceof Date ? value : new Date(value);
    return date.toLocaleString(undefined, {
        month: 'short',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
    });
}
