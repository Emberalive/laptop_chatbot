// utils/formatters.js
export function formatPrice(price) {
    if (!price) return 'Not specified';
    return price.replace(/Â/g, '');
}

export function formatSpecValue(value) {
    if (!value) return 'Not specified';
    if (typeof value === 'boolean') return value ? 'Yes' : 'No';
    return value;
}