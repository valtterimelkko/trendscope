#!/usr/bin/env python3
"""
Apply Brand Tokens to Template

Reads brand values from Brand Kit and updates template CSS tokens and Tailwind config.

Usage:
    python3 apply-brand-tokens.py --template templates/analytics-dashboard --brand-kit docs/brand/brand-kit-guide.md
    python3 apply-brand-tokens.py --template templates/analytics-dashboard --brand-kit docs/brand/brand-kit-guide.md --validate
"""

import argparse
import re
import json
import os
import sys
from pathlib import Path


def hex_to_rgb(hex_color: str) -> tuple:
    """Convert hex color to RGB tuple."""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def rgb_to_hex(rgb: tuple) -> str:
    """Convert RGB tuple to hex color."""
    return '#{:02x}{:02x}{:02x}'.format(*rgb)


def hex_to_hsl(hex_color: str) -> tuple:
    """Convert hex color to HSL tuple."""
    r, g, b = [x / 255.0 for x in hex_to_rgb(hex_color)]
    max_c = max(r, g, b)
    min_c = min(r, g, b)
    l = (max_c + min_c) / 2
    
    if max_c == min_c:
        h = s = 0
    else:
        d = max_c - min_c
        s = d / (2 - max_c - min_c) if l > 0.5 else d / (max_c + min_c)
        
        if max_c == r:
            h = (g - b) / d + (6 if g < b else 0)
        elif max_c == g:
            h = (b - r) / d + 2
        else:
            h = (r - g) / d + 4
        h /= 6
    
    return (h * 360, s * 100, l * 100)


def hsl_to_hex(h: float, s: float, l: float) -> str:
    """Convert HSL to hex color."""
    h, s, l = h / 360, s / 100, l / 100
    
    if s == 0:
        r = g = b = l
    else:
        def hue_to_rgb(p, q, t):
            if t < 0: t += 1
            if t > 1: t -= 1
            if t < 1/6: return p + (q - p) * 6 * t
            if t < 1/2: return q
            if t < 2/3: return p + (q - p) * (2/3 - t) * 6
            return p
        
        q = l * (1 + s) if l < 0.5 else l + s - l * s
        p = 2 * l - q
        r = hue_to_rgb(p, q, h + 1/3)
        g = hue_to_rgb(p, q, h)
        b = hue_to_rgb(p, q, h - 1/3)
    
    return '#{:02x}{:02x}{:02x}'.format(int(r * 255), int(g * 255), int(b * 255))


def generate_color_variants(hex_color: str) -> dict:
    """Generate hover and light variants of a color."""
    h, s, l = hex_to_hsl(hex_color)
    
    return {
        'default': hex_color,
        'hover': hsl_to_hex(h, s, max(0, l - 10)),
        'light': hsl_to_hex(h, max(10, s - 30), min(95, l + 35)),
    }


def calculate_contrast_ratio(color1: str, color2: str) -> float:
    """Calculate WCAG contrast ratio between two colors."""
    def relative_luminance(hex_color: str) -> float:
        r, g, b = [x / 255.0 for x in hex_to_rgb(hex_color)]
        
        def adjust(c):
            return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
        
        return 0.2126 * adjust(r) + 0.7152 * adjust(g) + 0.0722 * adjust(b)
    
    l1 = relative_luminance(color1)
    l2 = relative_luminance(color2)
    
    lighter = max(l1, l2)
    darker = min(l1, l2)
    
    return (lighter + 0.05) / (darker + 0.05)


def extract_colors_from_brand_kit(brand_kit_path: str) -> dict:
    """Extract color values from Brand Kit markdown file."""
    colors = {
        'primary': None,
        'secondary': None,
        'accent': None,
        'background': '#FFFFFF',
        'foreground': '#0F172A',
    }
    
    with open(brand_kit_path, 'r') as f:
        content = f.read()
    
    # Look for hex colors in the document
    hex_pattern = r'#[0-9A-Fa-f]{6}'
    
    # Try to find labeled colors
    primary_match = re.search(r'[Pp]rimary.*?(' + hex_pattern + ')', content)
    secondary_match = re.search(r'[Ss]econdary.*?(' + hex_pattern + ')', content)
    accent_match = re.search(r'[Aa]ccent.*?(' + hex_pattern + ')', content)
    
    if primary_match:
        colors['primary'] = primary_match.group(1)
    if secondary_match:
        colors['secondary'] = secondary_match.group(1)
    if accent_match:
        colors['accent'] = accent_match.group(1)
    
    # If no labeled colors found, use first hex colors found
    all_colors = re.findall(hex_pattern, content)
    if all_colors:
        if not colors['primary'] and len(all_colors) > 0:
            colors['primary'] = all_colors[0]
        if not colors['secondary'] and len(all_colors) > 1:
            colors['secondary'] = all_colors[1]
        if not colors['accent'] and len(all_colors) > 2:
            colors['accent'] = all_colors[2]
    
    # Use primary as secondary/accent if not found
    if colors['primary']:
        if not colors['secondary']:
            colors['secondary'] = colors['primary']
        if not colors['accent']:
            colors['accent'] = colors['primary']
    
    return colors


def extract_fonts_from_brand_kit(brand_kit_path: str) -> dict:
    """Extract font families from Brand Kit markdown file."""
    fonts = {
        'display': '"Inter", ui-sans-serif, system-ui, sans-serif',
        'body': '"Inter", ui-sans-serif, system-ui, sans-serif',
        'mono': '"JetBrains Mono", ui-monospace, monospace',
    }
    
    with open(brand_kit_path, 'r') as f:
        content = f.read()
    
    # Look for font family mentions
    font_pattern = r'(?:font|typeface|typography).*?["\']?([A-Za-z\s]+)["\']?'
    
    heading_match = re.search(r'[Hh]eading.*?' + font_pattern, content, re.IGNORECASE)
    body_match = re.search(r'[Bb]ody.*?' + font_pattern, content, re.IGNORECASE)
    
    if heading_match:
        font_name = heading_match.group(1).strip()
        fonts['display'] = f'"{font_name}", ui-sans-serif, system-ui, sans-serif'
    
    if body_match:
        font_name = body_match.group(1).strip()
        fonts['body'] = f'"{font_name}", ui-sans-serif, system-ui, sans-serif'
    
    return fonts


def update_tokens_css(template_path: str, colors: dict, fonts: dict) -> bool:
    """Update the tokens.css file with brand colors and fonts."""
    tokens_path = Path(template_path) / 'frontend' / 'styles' / 'tokens.css'
    
    if not tokens_path.exists():
        print(f"ERROR: tokens.css not found at {tokens_path}")
        return False
    
    with open(tokens_path, 'r') as f:
        content = f.read()
    
    # Generate color variants
    if colors['primary']:
        variants = generate_color_variants(colors['primary'])
        content = re.sub(r'--color-primary:\s*[^;]+;', f'--color-primary: {variants["default"]};', content)
        content = re.sub(r'--color-primary-hover:\s*[^;]+;', f'--color-primary-hover: {variants["hover"]};', content)
        content = re.sub(r'--color-primary-light:\s*[^;]+;', f'--color-primary-light: {variants["light"]};', content)
    
    if colors['secondary']:
        variants = generate_color_variants(colors['secondary'])
        content = re.sub(r'--color-secondary:\s*[^;]+;', f'--color-secondary: {variants["default"]};', content)
        content = re.sub(r'--color-secondary-hover:\s*[^;]+;', f'--color-secondary-hover: {variants["hover"]};', content)
    
    if colors['accent']:
        variants = generate_color_variants(colors['accent'])
        content = re.sub(r'--color-accent:\s*[^;]+;', f'--color-accent: {variants["default"]};', content)
        content = re.sub(r'--color-accent-hover:\s*[^;]+;', f'--color-accent-hover: {variants["hover"]};', content)
    
    # Update fonts
    content = re.sub(r'--font-display:\s*[^;]+;', f'--font-display: {fonts["display"]};', content)
    content = re.sub(r'--font-body:\s*[^;]+;', f'--font-body: {fonts["body"]};', content)
    content = re.sub(r'--font-mono:\s*[^;]+;', f'--font-mono: {fonts["mono"]};', content)
    
    with open(tokens_path, 'w') as f:
        f.write(content)
    
    print(f"✓ Updated {tokens_path}")
    return True


def validate_accessibility(colors: dict) -> list:
    """Validate color contrast ratios for accessibility."""
    issues = []
    
    if colors['primary'] and colors['background']:
        ratio = calculate_contrast_ratio(colors['primary'], colors['background'])
        if ratio < 4.5:
            issues.append(f"Primary on background: {ratio:.2f}:1 (needs 4.5:1)")
        else:
            print(f"✓ Primary on background: {ratio:.2f}:1 (PASS)")
    
    if colors['foreground'] and colors['background']:
        ratio = calculate_contrast_ratio(colors['foreground'], colors['background'])
        if ratio < 4.5:
            issues.append(f"Foreground on background: {ratio:.2f}:1 (needs 4.5:1)")
        else:
            print(f"✓ Foreground on background: {ratio:.2f}:1 (PASS)")
    
    return issues


def main():
    parser = argparse.ArgumentParser(description='Apply brand tokens to template')
    parser.add_argument('--template', required=True, help='Path to template directory')
    parser.add_argument('--brand-kit', required=True, help='Path to brand kit markdown file')
    parser.add_argument('--validate', action='store_true', help='Validate accessibility after applying')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.brand_kit):
        print(f"ERROR: Brand kit not found at {args.brand_kit}")
        sys.exit(1)
    
    if not os.path.exists(args.template):
        print(f"ERROR: Template not found at {args.template}")
        sys.exit(1)
    
    print("Extracting brand values...")
    colors = extract_colors_from_brand_kit(args.brand_kit)
    fonts = extract_fonts_from_brand_kit(args.brand_kit)
    
    print(f"\nExtracted colors:")
    for name, value in colors.items():
        print(f"  {name}: {value}")
    
    print(f"\nExtracted fonts:")
    for name, value in fonts.items():
        print(f"  {name}: {value}")
    
    print("\nUpdating tokens.css...")
    success = update_tokens_css(args.template, colors, fonts)
    
    if not success:
        sys.exit(1)
    
    if args.validate:
        print("\nValidating accessibility...")
        issues = validate_accessibility(colors)
        
        if issues:
            print("\n⚠ Accessibility issues found:")
            for issue in issues:
                print(f"  - {issue}")
        else:
            print("\n✓ All accessibility checks passed")
    
    print("\n✓ Brand tokens applied successfully")


if __name__ == '__main__':
    main()
