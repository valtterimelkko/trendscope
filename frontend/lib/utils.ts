import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/**
 * Validates if a string is a valid UUID v4
 * Used for path parameter validation in API routes
 */
const UUID_REGEX = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

export function isUuid(value: string): boolean {
  return UUID_REGEX.test(value);
}

/**
 * Validates UUID and throws appropriate error message
 * Returns true if valid, false if invalid
 */
export function validateUuid(value: string, fieldName: string = 'ID'): { valid: boolean; error?: string } {
  if (!value || typeof value !== 'string') {
    return { valid: false, error: `${fieldName} is required` };
  }
  if (!isUuid(value)) {
    return { valid: false, error: `Invalid ${fieldName.toLowerCase()} format` };
  }
  return { valid: true };
}
